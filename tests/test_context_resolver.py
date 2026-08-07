"""Tests for ContextResolver and heuristic ranking."""

from __future__ import annotations

from app.artifacts.models import Artifact, ExecutionArtifactType
from app.context.models import ContextEntry, ContextRole, ContextSource
from app.context.resolver import ContextResolver


def test_context_resolver_explicit_id_match():
    resolver = ContextResolver()
    history = [ContextEntry(ContextRole.USER, ContextSource.USER, "read a file")]
    
    a1 = Artifact("ART-001", "REQ-1", ExecutionArtifactType.TEXT, "doc1.txt", "content of doc 1")
    a2 = Artifact("ART-002", "REQ-1", ExecutionArtifactType.TEXT, "doc2.txt", "content of doc 2")

    # User explicitly asks for ART-002
    resolved = resolver.resolve("summarize ART-002 please", history, [a1, a2])
    assert len(resolved.artifacts) == 1
    assert resolved.artifacts[0].id == "ART-002"

    # User explicitly asks for art-1 (short/case-insensitive match)
    resolved = resolver.resolve("summarize art-1", history, [a1, a2])
    assert len(resolved.artifacts) == 1
    assert resolved.artifacts[0].id == "ART-001"


def test_context_resolver_name_match():
    resolver = ContextResolver()
    history = []
    
    a1 = Artifact("ART-001", "REQ-1", ExecutionArtifactType.TEXT, "README.md", "SentinelAI info")
    a2 = Artifact("ART-002", "REQ-1", ExecutionArtifactType.TEXT, "notes.txt", "some personal notes")

    resolved = resolver.resolve("summarize README", history, [a1, a2])
    assert len(resolved.artifacts) == 1
    assert resolved.artifacts[0].id == "ART-001"


def test_context_resolver_recency_boost():
    resolver = ContextResolver()
    history = []
    
    # a2 is newer than a1
    a1 = Artifact("ART-001", "REQ-1", ExecutionArtifactType.TEXT, "old.txt", "old", timestamp=100.0)
    a2 = Artifact("ART-002", "REQ-1", ExecutionArtifactType.TEXT, "new.txt", "new", timestamp=200.0)

    # Generic reference "summarize it"
    resolved = resolver.resolve("summarize it", history, [a1, a2])
    assert len(resolved.artifacts) == 1
    assert resolved.artifacts[0].id == "ART-002"
