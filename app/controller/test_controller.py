from app.controller.assistant_controller import AssistantController 

def test_process_message():
    controller = AssistantController()
    
    response = controller.process_message("Hello, Sentinel AI!")
    
    assert isinstance(response, str)