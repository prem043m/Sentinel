from app.planner.registry import CommandRegistry


def test_calculator():

    registry = CommandRegistry()

    plan = registry.match("open calculator")

    assert plan is not None
    assert plan.parameters["name"] == "Calculator"


def test_notepad():

    registry = CommandRegistry()

    plan = registry.match("open notepad")

    assert plan.parameters["name"] == "Notepad"


def test_chrome():

    registry = CommandRegistry()

    plan = registry.match("open chrome")

    assert plan.parameters["name"] == "Google Chrome"