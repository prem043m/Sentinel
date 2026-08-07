from app.utils.logger import setup_logger
from app.controller.assistant_controller import AssistantController

def main():
    logger = setup_logger()
    controller = AssistantController()
    
    print("SentinelAI is starting...")
    print("Performing Ollama model health check and warming up...")
    
    status = controller.warm_up()
    
    print("\n=== Ollama Model Health status ===")
    print(f"Connected to Ollama : {'Yes' if status.get('connected') else 'No'}")
    print(f"Model installed     : {'Yes' if status.get('model_installed') else 'No'}")
    print(f"Model Warmed (RAM)  : {'Yes' if status.get('warm') else 'No'}")
    
    details = status.get("details", {})
    if details:
        model_info = details.get("details", {})
        print(f"Format              : {model_info.get('format', 'Unknown')}")
        print(f"Family              : {model_info.get('family', 'Unknown')}")
        print(f"Parameter Size      : {details.get('parameters', 'Unknown') or model_info.get('parameter_size', 'Unknown')}")
        print(f"Quantization Level  : {model_info.get('quantization_level', 'Unknown')}")
    print("==================================\n")
    
    print("Type 'exit' to quit the application.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            logger.info("SentinelAI shutting down.")
            print("Exiting SentinelAI. Goodbye!")
            break

        if user_input.lower() == "clear":
            controller.context_manager.clear()
            print("SentinelAI: Session context cleared.\n")
            continue

        response = controller.process_message(user_input)
        
        print(f"SentinelAI: {response}\n")

if __name__ == "__main__":
    main()