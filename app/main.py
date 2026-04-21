from app.config import get_settings # Import the get_settings function from the config module to load configuration settings.


def main() -> None:
    settings = get_settings()
    print("Chat model:", settings.openai_chat_model)
    print("Embedding model:", settings.openai_embedding_model)
    print("Chroma dir:", settings.chroma_persist_dir)
    print("SQL string loaded:", bool(settings.sql_server_connection_string))


if __name__ == "__main__":
    main()