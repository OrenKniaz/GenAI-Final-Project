# GenAI-Final-Project

## Project Goal

This project builds a Python-based recruiting chatbot. The bot should decide whether to continue the conversation, schedule an interview, or end the conversation.

The app uses:
- Python
- LangChain
- OpenAI API
- SQL Server for interview availability
- Streamlit for the frontend

## Current Status

- `.env` is set up locally.
- `app/config.py` is ready and loads environment settings.
- `app/modules/Helpers/sql_helper.py` is ready and tested against the `Tech` database.
- `app/modules/agent_router.py` is now wired to the three advisors and returns CONTINUE, SCHEDULE, or END.
- `app/modules/exit_advisor.py`, `app/modules/schedule_advisor.py`, and `app/modules/info_advisor.py` are in place as the first advisor layer.
- `app/main.py` is ready and prints the loaded config values, routes a sample message, and only calls SQL when the action is scheduling.
- The backend smoke test now loads config, runs the router, and only calls SQL when the router returns a scheduling action.
- Chroma is planned later, but it is not wired in yet.
- `streamlit_app/streamlit_main.py` is the first Streamlit UI slice and uses the same router as the backend smoke test.
- Streamlit currently runs with `PYTHONPATH="C:\\GenAI Final Project"` so the `app` package can be imported from the repo root.

## `.env` Format

Use a local `.env` file with this shape:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
SQL_SERVER_CONNECTION_STRING=your_sql_server_connection_string
CHROMA_PERSIST_DIR=./chroma_db
```

The `.env` file itself is ignored by Git.

## Project Structure

- `app/` - backend entry point and config loader
- `streamlit_app/` - Streamlit frontend
- `Database/` - SQL and sample data
- `Docs/` - project assignment material

## Notes

- The config module is the single place that reads environment variables.
- `app/main.py` is still a small startup/smoke test entry point.
- `streamlit_app/streamlit_main.py` is the current frontend entrypoint for the demo UI.
- `app/modules/agent_router.py` is a temporary rule-based coordinator for the first agent slice.
- Chroma will be added later when the retrieval part of the bot is built.
