from app.controller.assistant_controller import AssistantController


class DummyPlan:
    def __init__(self, intent, parameters):
        self.intent = intent
        self.parameters = parameters


class DummyPlanner:
    def __init__(self, plan):
        self.plan = plan
        self.received_message = None

    def create_plan(self, message: str):
        self.received_message = message
        return self.plan


class DummyLLM:
    def __init__(self):
        self.received_prompt = None

    def generate(self, prompt: str):
        self.received_prompt = prompt
        return "llm-response"


class DummyExecutor:
    def __init__(self):
        self.received_plan = None

    def execute(self, plan):
        self.received_plan = plan
        return type("Result", (), {"message": "executed-plan"})()


def test_process_message_routes_chat_to_llm():
    plan = DummyPlan("chat", {"prompt": "Hello"})
    planner = DummyPlanner(plan)
    llm = DummyLLM()
    executor = DummyExecutor()
    controller = AssistantController(planner=planner, executor=executor, llm=llm)

    response = controller.process_message("Hello")

    assert response == "llm-response"
    assert planner.received_message == "Hello"
    assert llm.received_prompt == "Hello"
    assert executor.received_plan is None


def test_process_message_returns_plan_created_for_non_chat():
    plan = DummyPlan("open_application", {"name": "Visual Studio Code"})
    planner = DummyPlanner(plan)
    llm = DummyLLM()
    executor = DummyExecutor()
    controller = AssistantController(planner=planner, executor=executor, llm=llm)

    response = controller.process_message("Open VS Code")

    assert response == "executed-plan"
    assert planner.received_message == "Open VS Code"
    assert llm.received_prompt is None
    assert executor.received_plan is plan