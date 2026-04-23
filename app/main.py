from app.config import get_settings # Import the get_settings function from the config module to load configuration settings.
from app.modules.Helpers.sql_helper import get_available_slots
from app.modules.agent_router import Action, decide_action


def main() -> None:

    # validate settings load.
    settings = get_settings()
    print("Chat model:", settings.openai_chat_model)
    print("Embedding model:", settings.openai_embedding_model)
    print("Chroma dir:", settings.chroma_persist_dir)

    # Use our simple agent router to decide what action to take based on a test message. This simulates how the agent would process user input and determine the next step.
    action = decide_action("Can we schedule an interview?")
    print("Decided action:", action)
    
    # If the action is SCHEDULE, call the SQL helper to retrieve and print available interview slots.
    if action == Action.SCHEDULE:
        slots = get_available_slots()
        print("Available slots:")
        for slot in slots:
            print(slot)
        


if __name__ == "__main__":
    main()