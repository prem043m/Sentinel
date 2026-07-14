"""Application allowlist for the ApplicationTool.

This module defines the trust boundary between Planner output and
Windows process execution.  Only applications explicitly listed here
may be launched by the ApplicationTool.

The allowlist uses a Python module (not JSON/YAML) for:
- Type safety
- Version control friendliness
- No parser dependencies
- Easy unit testing
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AllowedApplication:
    """An application that SentinelAI is permitted to launch.

    Attributes:
        name: The canonical display name (e.g. ``"Calculator"``).
        executable: The Windows executable name or command
                    (e.g. ``"calc.exe"``).  Must be resolvable on
                    the system PATH or be an absolute path.
    """

    name: str
    executable: str


# ── Allowlist ──────────────────────────────────────────────────────
# Every entry maps a *normalised lowercase* display name to its
# AllowedApplication definition.  Lookup is always case-insensitive;
# callers must normalise their query with ``str.lower()`` before
# hitting this dict.

_ALLOWLIST: dict[str, AllowedApplication] = {
    "calculator": AllowedApplication(
        name="Calculator",
        executable="calc.exe",
    ),
    "notepad": AllowedApplication(
        name="Notepad",
        executable="notepad.exe",
    ),
    "google chrome": AllowedApplication(
        name="Google Chrome",
        executable="chrome.exe",
    ),
    "visual studio code": AllowedApplication(
        name="Visual Studio Code",
        executable="code.cmd",
    ),
}


def lookup(name: str) -> AllowedApplication | None:
    """Look up an application by its friendly name.

    The lookup is **case-insensitive**.  Leading and trailing
    whitespace is stripped before matching.

    Args:
        name: The user-facing application name
              (e.g. ``"Calculator"``, ``"calculator"``, ``"CALCULATOR"``).

    Returns:
        The matching ``AllowedApplication`` if the name is in the
        allowlist, or ``None`` if it is not permitted.
    """
    return _ALLOWLIST.get(name.strip().lower())
