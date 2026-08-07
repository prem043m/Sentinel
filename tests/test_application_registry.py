from app.tools.application.database import ApplicationDatabase
from app.tools.application.models import Application, ApplicationSource, build_application_id
from app.tools.application.registry import ApplicationRegistry
from app.tools.application.resolver import ApplicationResolver


def _application(name: str, path: str, *, aliases=(), approved=False) -> Application:
    return Application(
        id=build_application_id(name, path, ApplicationSource.REGISTRY),
        name=name,
        path=path,
        aliases=aliases,
        approved=approved,
        source=ApplicationSource.REGISTRY,
    )


def test_registry_returns_only_approved_applications(tmp_path):
    database = ApplicationDatabase(
        file_path=tmp_path / "applications.json",
        seed=(
            _application("Calculator", "calc.exe", approved=True),
            _application("Steam", r"C:\\Steam\\steam.exe"),
        ),
    )

    registry = ApplicationRegistry(database=database, resolver=ApplicationResolver())

    assert [application.name for application in registry.all()] == ["Calculator"]
    assert registry.lookup("calculator").name == "Calculator"
    assert registry.lookup("Steam") is None


def test_registry_supports_alias_and_fuzzy_lookup(tmp_path):
    database = ApplicationDatabase(
        file_path=tmp_path / "applications.json",
        seed=(
            _application("Visual Studio Code", r"C:\\VSCode\\Code.exe", aliases=("vs code", "vscode"), approved=True),
        ),
    )

    registry = ApplicationRegistry(database=database, resolver=ApplicationResolver())

    assert registry.lookup("vs code").name == "Visual Studio Code"
    assert registry.lookup("vscode").name == "Visual Studio Code"
    assert registry.lookup("vsiual studio code").name == "Visual Studio Code"