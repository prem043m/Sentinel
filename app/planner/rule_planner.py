import re
from copy import deepcopy

from app.models.plan import Plan
from app.planner.commands import COMMANDS
from app.planner.strategy import PlannerStrategy


class RulePlanner(PlannerStrategy):
    def create_plan(self, user_input: str) -> Plan:
        for command in COMMANDS:
            if self._matches(command["patterns"], user_input):
                return deepcopy(command["plan"])

        # ── Browser: open URL ─────────────────────────────────────
        url_match = re.search(
            r"(?:open|go\s+to|browse|visit|navigate\s+to)\s+"
            r"((?:https?://)\S+)",
            user_input,
            re.IGNORECASE,
        )

        if not url_match:
            # Match bare domains like "open google.com"
            url_match = re.search(
                r"(?:open|go\s+to|browse|visit|navigate\s+to)\s+"
                r"(\S+\.\S+)",
                user_input,
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
            user_input,
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
            user_input,
            re.IGNORECASE,
        )

        if file_match:
            return Plan(
                intent="read_file",
                tool="filesystem",
                parameters={"path": file_match.group(1)},
            )

        # ── Filesystem: list directory ────────────────────────────
        list_match = re.search(
            r"list(?:\s+(?:directory|files\s+in))?\s+(.+)",
            user_input,
            re.IGNORECASE,
        )

        if list_match:
            return Plan(
                intent="list_directory",
                tool="filesystem",
                parameters={"path": list_match.group(1)},
            )

        return Plan(
            intent="chat",
            tool="llm",
            parameters={"prompt": user_input},
        )

    @staticmethod
    def _matches(patterns: list[str], text: str) -> bool:
        normalized_text = text.lower().strip()

        for pattern in patterns:
            if re.search(pattern, normalized_text):
                return True

        return False
