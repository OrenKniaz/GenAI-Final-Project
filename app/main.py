from app.config import get_settings # Import the get_settings function from the config module to load configuration settings.
from app.modules.Helpers.sql_helper import get_available_slots


def main() -> None:
    settings = get_settings()
    print("Chat model:", settings.openai_chat_model)
    print("Embedding model:", settings.openai_embedding_model)
    print("Chroma dir:", settings.chroma_persist_dir)

    slots = get_available_slots(limit=5)
    print("Available slots:")
    for slot in slots:
        print(slot)


if __name__ == "__main__":
    main()