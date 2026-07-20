from app.models.plan import Plan
from app.policy.engine import PolicyEngine
from app.policy.risk import RiskLevel


def test_chat_allowed():
    engine = PolicyEngine()

    plan = Plan(
        intent="chat",
        tool="llm",
        parameters={}
    )

    decision = engine.evaluate(plan)

    assert decision.allowed
    assert decision.risk == RiskLevel.LOW


def test_open_browser_allowed():
    engine = PolicyEngine()

    plan = Plan(
        intent="open_browser",
        tool="browser",
        parameters={}
    )

    decision = engine.evaluate(plan)

    assert decision.allowed
    assert decision.risk == RiskLevel.LOW
    assert not decision.confirmation_required


def test_open_url_allowed():
    engine = PolicyEngine()
    plan = Plan(intent="open_url", tool="browser", parameters={})
    decision = engine.evaluate(plan)
    assert decision.allowed
    assert decision.risk == RiskLevel.LOW
    assert not decision.confirmation_required


def test_search_web_allowed():
    engine = PolicyEngine()
    plan = Plan(intent="search_web", tool="browser", parameters={})
    decision = engine.evaluate(plan)
    assert decision.allowed
    assert decision.risk == RiskLevel.LOW
    assert not decision.confirmation_required


def test_create_folder_allowed():
    engine = PolicyEngine()

    plan = Plan(
        intent="create_folder",
        tool="filesystem",
        parameters={}
    )

    decision = engine.evaluate(plan)

    assert decision.allowed
    assert decision.risk == RiskLevel.MEDIUM
    assert not decision.confirmation_required

def test_list_directory_allowed():
    engine = PolicyEngine()
    plan = Plan(intent="list_directory", tool="filesystem", parameters={})
    decision = engine.evaluate(plan)
    assert decision.allowed
    assert decision.risk == RiskLevel.MEDIUM
    assert not decision.confirmation_required


def test_delete_folder_requires_confirmation():
    engine = PolicyEngine()

    plan = Plan(
        intent="delete_folder",
        tool="filesystem",
        parameters={}
    )

    decision = engine.evaluate(plan)

    assert decision.allowed
    assert decision.risk == RiskLevel.HIGH
    assert decision.confirmation_required


def test_shutdown_system_requires_confirmation():
    engine = PolicyEngine()

    plan = Plan(
        intent="shutdown_system",
        tool="system",
        parameters={}
    )

    decision = engine.evaluate(plan)

    assert decision.allowed
    assert decision.risk == RiskLevel.CRITICAL
    assert decision.confirmation_required
