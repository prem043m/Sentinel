from app.models.plan import Plan

def test_plan_creation():
    plan = Plan(
        intent="open_application",
        tool="application",
        parameters={"name": "Calculator"},
    )
    assert plan.intent == "open_application"
    assert plan.tool == "application"
    assert plan.parameters['name'] ==  "Calculator"