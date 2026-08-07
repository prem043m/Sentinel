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


def test_open_calculator_plan_handles_typo():
    planner = RulePlanner()

    plan = planner.create_plan("opne calculator")

    assert plan.intent == "open_application"
    assert plan.tool == "application"
    assert plan.parameters["name"] == "Calculator"


def test_open_vs_code_plan():
    planner = RulePlanner()

    plan = planner.create_plan("open vs code")

    assert plan.intent == "open_application"
    assert plan.tool == "application"
    assert plan.parameters["name"] == "Visual Studio Code"


def test_read_file_plan():

    planner = RulePlanner()

    plan = planner.create_plan("read file notes.txt")

    assert plan.intent == "read_file"
    assert plan.tool == "filesystem"
    assert plan.parameters["path"] == "notes.txt"

def test_list_directory_plan():
    planner = RulePlanner()
    plan = planner.create_plan("list files in D:\\Projects")
    
    assert plan.intent == "list_directory"
    assert plan.tool == "filesystem"
    assert plan.parameters["path"] == "D:\\Projects"

def test_open_url_plan():
    planner = RulePlanner()
    plan = planner.create_plan("open https://github.com")
    assert plan.intent == "open_url"
    assert plan.tool == "browser"
    assert plan.parameters["url"] == "https://github.com"


def test_open_github_profile_path_plan():
    planner = RulePlanner()

    plan = planner.create_plan("open github/prem043m")

    assert plan.intent == "open_url"
    assert plan.tool == "browser"
    assert plan.parameters["url"] == "https://github.com/prem043m"

def test_open_bare_domain_plan():
    planner = RulePlanner()
    plan = planner.create_plan("open google.com")
    assert plan.intent == "open_url"
    assert plan.tool == "browser"
    assert plan.parameters["url"] == "google.com"

def test_go_to_url_plan():
    planner = RulePlanner()
    plan = planner.create_plan("go to https://example.com")
    assert plan.intent == "open_url"
    assert plan.tool == "browser"
    assert plan.parameters["url"] == "https://example.com"

def test_search_web_plan():
    planner = RulePlanner()
    plan = planner.create_plan("search for Python tutorials")
    assert plan.intent == "search_web"
    assert plan.tool == "browser"
    assert plan.parameters["query"] == "Python tutorials"

def test_google_query_plan():
    planner = RulePlanner()
    plan = planner.create_plan("google machine learning")
    assert plan.intent == "search_web"
    assert plan.tool == "browser"
    assert plan.parameters["query"] == "machine learning"