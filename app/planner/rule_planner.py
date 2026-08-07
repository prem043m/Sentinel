from difflib import get_close_matches
import re
from copy import deepcopy

from app.models.plan import Plan, PlanOutcome
from app.planner.commands import COMMANDS
from app.planner.strategy import PlannerStrategy


class RulePlanner(PlannerStrategy):
    def create_plan(self, user_input: str) -> Plan:
        normalized_input = self._normalize_command_text(user_input)

        # Check for recognized domain but unsupported operations (Unsupported Capability)
        unsupported_rules = [
            (r"\b(delete|remove|rm|erase|destroy)\b", "File deletion is not supported."),
            (r"\b(copy|cp|duplicate|clone)\b", "File copying is not supported."),
            (r"\b(move|mv|rename)\b", "File moving/renaming is not supported."),
            (r"\b(write|create|make|touch|mkdir|edit|modify)\s+(file|directory|folder)\b", "Creating/modifying files or directories is not supported."),
            (r"\b(shutdown|restart|reboot|logoff|log\s*out|lock|sleep|hibernate)\b", "System power actions are not supported."),
            (r"\b(refresh|reload)\s+(applications|apps)\b", "Refreshing applications registry is not supported."),
            (r"\b(install|uninstall)\s+(app|application|program|software)\b", "Installing or uninstalling applications is not supported."),
        ]

        normalized_lower = normalized_input.lower()
        for pattern, reason in unsupported_rules:
            if re.search(pattern, normalized_lower):
                return Plan(
                    intent="unsupported_operation",
                    tool="unknown",
                    parameters={"query": user_input, "reason": reason},
                    outcome=PlanOutcome.UNSUPPORTED,
                )

        for command in COMMANDS:
            if self._matches(command["patterns"], normalized_input):
                return deepcopy(command["plan"])

        github_match = re.search(
            r"(?:open|go\s+to|browse|visit|navigate\s+to)\s+"
            r"(?:https?://)?(?:www\.)?(?:gitub|github)(?:\.com)?/(\S+)",
            normalized_input,
            re.IGNORECASE,
        )

        if github_match:
            return Plan(
                intent="open_url",
                tool="browser",
                parameters={"url": f"https://github.com/{github_match.group(1).lstrip('/')}"},
            )

        # ── Browser: open URL ─────────────────────────────────────
        url_match = re.search(
            r"(?:open|go\s+to|browse|visit|navigate\s+to)\s+"
            r"((?:https?://)\S+)",
            normalized_input,
            re.IGNORECASE,
        )

        if not url_match:
            # Match bare domains like "open google.com"
            url_match = re.search(
                r"(?:open|go\s+to|browse|visit|navigate\s+to)\s+"
                r"(\S+\.\S+)",
                normalized_input,
                re.IGNORECASE,
            )

        if url_match:
            return Plan(
                intent="open_url",
                tool="browser",
                parameters={"url": url_match.group(1)},
            )

        # ── Browser: search web ───────────────────────────────────
        search_match = re.search(
            r"(?:search(?:\s+for)?|google)\s+(.+)",
            normalized_input,
            re.IGNORECASE,
        )

        if search_match:
            return Plan(
                intent="search_web",
                tool="browser",
                parameters={"query": search_match.group(1)},
            )

        # ── Filesystem: read file ─────────────────────────────────
        file_match = re.search(
            r"read(?:\s+file)?\s+(.+)",
            normalized_input,
            re.IGNORECASE,
        )

        if file_match:
            return Plan(
                intent="read_file",
                tool="filesystem",
                parameters={"path": self._normalize_path(file_match.group(1))},
            )

        # ── Filesystem: list directory ────────────────────────────
        list_match = re.search(
            r"list(?:\s+(?:directory|files\s+in))?\s+(.+)",
            normalized_input,
            re.IGNORECASE,
        )

        if list_match:
            return Plan(
                intent="list_directory",
                tool="filesystem",
                parameters={"path": self._normalize_path(list_match.group(1))},
            )

        return Plan(
            intent="chat",
            tool="llm",
            parameters={"prompt": user_input},
            outcome=PlanOutcome.CHAT,
        )

    @staticmethod
    def _matches(patterns: list[str], text: str) -> bool:
        normalized_text = text.lower().strip()

        for pattern in patterns:
            if re.search(pattern, normalized_text):
                return True

        return False

    @staticmethod
    def _normalize_command_text(text: str) -> str:
        """Normalize common one-word typos in the leading command verb."""
        tokens = text.split(maxsplit=1)
        if not tokens:
            return text

        command_verbs = [
            "open",
            "launch",
            "start",
            "search",
            "google",
            "read",
            "list",
            "go",
            "browse",
            "visit",
            "navigate",
        ]
        match = get_close_matches(tokens[0].lower(), command_verbs, n=1, cutoff=0.75)
        if not match:
            return text

        if len(tokens) == 1:
            return match[0]

        return f"{match[0]} {tokens[1]}"

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Normalize extracted file path string (e.g. 'the README.md file' -> 'README.md')."""
        path = path.strip()
        # Strip leading "the "
        if path.lower().startswith("the "):
            path = path[4:].strip()
        # Strip trailing " file" or " files"
        if path.lower().endswith(" file"):
            path = path[:-5].strip()
        elif path.lower().endswith(" files"):
            path = path[:-6].strip()
        # Strip trailing punctuation
        path = path.rstrip(".?")
        return path
