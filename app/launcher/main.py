from app.utils.logger import setup_logger
from app.controller.assistant_controller import AssistantController

def main():
    logger = setup_logger()
    controller = AssistantController()
    
    print("SentinelAI is starting....")
    print("Type 'exit' to quit the application.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            logger.info("SentinelAI shutting down.")
            print("Exiting SentinelAI. Goodbye!")
            break

        response = controller.process_message(user_input)
        
        print(f"SentinelAI: {response}\n")

if __name__ == "__main__":
    main()