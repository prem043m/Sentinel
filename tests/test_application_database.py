from app.tools.application.database import ApplicationDatabase
from app.tools.application.models import Application, ApplicationSource, build_application_id


def _application(name: str, path: str, approved: bool = False) -> Application:
    return Application(
        id=build_application_id(name, path, ApplicationSource.REGISTRY),
        name=name,
        path=path,
        aliases=(name.lower(),),
        approved=approved,
        source=ApplicationSource.REGISTRY,
    )


def test_database_round_trip(tmp_path):
    database_path = tmp_path / "applications.json"
    first = _application("Calculator", "calc.exe", approved=True)
    second = _application("Steam", r"C:\\Program Files\\Steam\\steam.exe")

    database = ApplicationDatabase(file_path=database_path, seed=(first,))
    database.add(second)

    reloaded = ApplicationDatabase(file_path=database_path)

    assert {application.name for application in reloaded.all()} == {"Calculator", "Steam"}
    assert database_path.exists()


def test_approval_updates_persist(tmp_path):
    database_path = tmp_path / "applications.json"
    application = _application("Discord", r"C:\\Discord\\Discord.exe")

    database = ApplicationDatabase(file_path=database_path, seed=(application,))
    updated = database.mark_approved(application.id)

    assert updated is not None
    assert updated.approved is True

    reloaded = ApplicationDatabase(file_path=database_path)
    persisted = reloaded.get(application.id)

    assert persisted is not None
    assert persisted.approved is True