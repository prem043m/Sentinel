"""Context resolution and ranking for SentinelAI.

Determines which conversation history and artifacts are relevant to the
user's current query, utilizing heuristics (recency, name matching, explicit ID
referencing, and token overlap).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Sequence

from app.artifacts.models import Artifact
from app.context.models import ContextEntry

logger = logging.getLogger("SentinelAI.ContextResolver")


@dataclass(frozen=True, slots=True)
class ResolvedContext:
    """The outcome of resolving session context for prompt generation.

    Attributes:
        conversation_history: Filtered sequence of conversation entries.
        artifacts: Ranked sequence of relevant artifacts to inject.
    """

    conversation_history: Sequence[ContextEntry]
    artifacts: Sequence[Artifact]


class ContextResolver:
    """Analyzes user requests to select and rank relevant context assets.

    Implements heuristics to determine if the user is referring to a file,
    directory, search result, or a general conversational context.
    """

    def resolve(
        self,
        user_query: str,
        history: Sequence[ContextEntry],
        artifacts: Sequence[Artifact],
    ) -> ResolvedContext:
        """Resolve and rank relevant history and artifacts for a query.

        Args:
            user_query: The current query entered by the user.
            history: The session's conversation history entries.
            artifacts: All artifacts in the session store.

        Returns:
            A :class:`ResolvedContext` containing the resolved history and
            ranked list of relevant artifacts.
        """
        if not artifacts:
            logger.debug("No artifacts in store to resolve.")
            return ResolvedContext(conversation_history=history, artifacts=[])

        query_lower = user_query.lower()
        scored_artifacts: list[tuple[float, Artifact]] = []

        # Find most recent artifact
        sorted_by_recency = sorted(artifacts, key=lambda a: a.timestamp, reverse=True)
        most_recent = sorted_by_recency[0] if sorted_by_recency else None

        # Check for generic reference keywords indicating the user refers to the last output
        reference_patterns = [
            r"\b(it|that|this|the file|the directory|the page|the results|the website|file|directory|folder|page|results|output)\b",
            r"\b(summarize|explain|show|describe|read|what is in|contents of|detail)\b"
        ]
        has_generic_reference = any(re.search(pat, query_lower) for pat in reference_patterns)

        for artifact in artifacts:
            score = 0.0

            # 1. Explicit ID match (e.g. ART-001 or ART-1)
            id_pattern = rf"\b{re.escape(artifact.id.lower())}\b"
            # Support short references (like "ART-1" when ID is "ART-001")
            numeric_id = "".join(filter(str.isdigit, artifact.id))
            short_id_pattern = rf"\bart-{int(numeric_id)}\b" if numeric_id else None

            if re.search(id_pattern, query_lower) or (short_id_pattern and re.search(short_id_pattern, query_lower)):
                score += 100.0
                logger.debug("Explicit ID match for %s (+100.0 score)", artifact.id)

            # 2. Name match (e.g. README.md)
            name_lower = artifact.name.lower()
            if name_lower and name_lower in query_lower:
                score += 50.0
                logger.debug("Name match for %s (+50.0 score)", artifact.id)
            else:
                # Partial name match (e.g. "README" matches "README.md")
                name_parts = [p for p in re.split(r"[._\-/\\]", name_lower) if len(p) > 2]
                for part in name_parts:
                    part_pattern = rf"\b{re.escape(part)}\b"
                    if re.search(part_pattern, query_lower):
                        score += 50.0
                        logger.debug("Partial name match '%s' for %s (+50.0 score)", part, artifact.id)

            # 3. Recency boost for generic reference
            if artifact == most_recent and has_generic_reference:
                score += 25.0
                logger.debug("Recency boost for %s (+25.0 score)", artifact.id)

            # 4. Content keyword overlap
            words = [
                w for w in re.findall(r"\b\w{3,}\b", query_lower)
                if w not in ("the", "and", "for", "that", "this", "with", "from", "are", "you")
            ]
            content_lower = artifact.content.lower()
            overlap_count = sum(1 for w in words if w in content_lower)
            if overlap_count > 0:
                overlap_score = min(overlap_count * 2.0, 20.0)
                score += overlap_score
                logger.debug("Content overlap count %d for %s (+%.1f score)", overlap_count, artifact.id, overlap_score)

            if score > 0.0:
                scored_artifacts.append((score, artifact))

        # If there are any explicit ID or name matches (score >= 50), ignore other generic matches (score < 50)
        has_explicit = any(item[0] >= 50.0 for item in scored_artifacts)
        if has_explicit:
            scored_artifacts = [item for item in scored_artifacts if item[0] >= 50.0]

        # Sort by score (descending), then by recency (timestamp descending)
        scored_artifacts.sort(key=lambda x: (x[0], x[1].timestamp), reverse=True)
        # Cap to top 1 artifact to prevent token bloat
        selected_artifacts = [item[1] for item in scored_artifacts][:1]

        # Log resolution result
        selected_ids = [a.id for a in selected_artifacts]
        rejected_ids = [a.id for a in artifacts if a.id not in selected_ids]
        logger.info(
            "ContextResolver: selected=%s, rejected=%s (query='%s')",
            selected_ids,
            rejected_ids,
            user_query[:50],
        )

        return ResolvedContext(
            conversation_history=history,
            artifacts=selected_artifacts,
        )
