from app.config import get_settings # Import the get_settings function from the config module to load configuration settings.
from app.modules.conversation_service import process_candidate_turn, CandidateTurnInput


def main() -> None:

    # validate settings load.
    settings = get_settings()
    print("Chat model:", settings.openai_chat_model)
    print("Embedding model:", settings.openai_embedding_model)
    print("Chroma dir:", settings.chroma_persist_dir)

    # Use our simple agent router to decide what action to take based on a test message. 
    turn = CandidateTurnInput(message="Can we schedule an interview?")
    result = process_candidate_turn(turn)
    
    # If the action is SCHEDULE, call the SQL helper to retrieve and print available interview slots.
    if result.show_slots and result.slots:
        print("Available slots:")
        for slot in result.slots:
            print(slot)
        


if __name__ == "__main__":
    main()