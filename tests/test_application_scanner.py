from pathlib import Path

from app.tools.application.models import ApplicationSource
from app.tools.application.scanner import ApplicationScanner


def test_scanner_discovers_executables_but_does_not_approve_them(tmp_path):
    install_root = tmp_path / "Program Files" / "Sample App"
    install_root.mkdir(parents=True)
    executable = install_root / "sample-app.exe"
    executable.write_text("binary placeholder", encoding="utf-8")

    scanner = ApplicationScanner(search_roots=[tmp_path], max_depth=4)
    applications = scanner.discover()

    assert any(application.path == str(executable) for application in applications)
    discovered = next(application for application in applications if application.path == str(executable))
    assert discovered.approved is False
    assert discovered.source in {ApplicationSource.UNKNOWN, ApplicationSource.PROGRAM_FILES, ApplicationSource.PROGRAM_FILES_X86}
    assert discovered.name == "Sample App"