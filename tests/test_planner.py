from app.planner.rule_planner import RulePlanner

def test_chat_plan():
    
    planner = RulePlanner()
    
    plan = planner.create_plan("Hello, how are you?")
    
    assert plan.intent == "chat"
    assert plan.tool == "llm"
    
def test_open_calculator_plan():
    
    planner = RulePlanner()
    
    plan = planner.create_plan("Open the calculator")
    assert plan.intent == "open_application"
    assert plan.tool == "application"


def test_read_file_plan():

    planner = RulePlanner()

    plan = planner.create_plan("read file notes.txt")

    assert plan.intent == "read_file"
    assert plan.tool == "filesystem"
    assert plan.parameters["path"] == "notes.txt"