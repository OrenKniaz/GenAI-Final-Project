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

- Phase 1 baseline architecture is complete.
- Phase 2 conversational Streamlit flow is complete.
- Phase 3 info-advisor work is in progress.
- `.env` is set up locally.
- `app/config.py` loads environment settings.
- `app/modules/Helpers/sql_helper.py` connects to the `Tech` database and returns available slots.
- `app/modules/agent_router.py` explicitly evaluates the exit, schedule, and info advisors and exposes both `route_message()` and `decide_action()`.
- `app/modules/conversation_service.py` now uses a shared turn contract, tracks the current role across turns, normalizes `Python Developer` to the SQL-facing `Python Dev` value, recovers role context from prior history, and sends `continue` turns through the OpenAI-backed info advisor.
- `app/modules/Helpers/llm_helper.py` centralizes `ChatOpenAI` construction.
- `app/modules/Helpers/history_helper.py` formats shared conversation history for advisor prompts.
- `app/modules/info_advisor.py` now uses LangChain/OpenAI to generate role answers with its own system prompt, few-shot examples, and shared conversation-history context.
- `app/main.py` and `streamlit_app/streamlit_main.py` both go through the same `process_candidate_turn()` backend flow.
- `streamlit_app/streamlit_main.py` now preserves multi-turn chat history in `st.session_state`, renders candidate and assistant turns in chat-style UI, shows the latest candidate message immediately, and displays an assistant-side `Thinking...` spinner while the model response is generated.
- Backend smoke verification passes.
- Streamlit manual verification passes, including contextual follow-up behavior through the info advisor.
- `tests/Code testing/test_conversation_service.py` now covers schedule, end, continue, advisor precedence, role detection, role normalization, carried-forward role state, neutral follow-up behavior, and role recovery from history.
- Chroma, retrieval, and grounded job-description answers are planned for later phases.

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
- `workplan.md` is now tracked in git and reflects phase and slice status.
- Chroma will be added later when the retrieval part of the bot is built.

## Testing

Run the conversation service test suite from the repo root:

```powershell
.\.venv\Scripts\python.exe -m unittest "tests/Code testing/test_conversation_service.py"
```

Run the Streamlit demo from the repo root:

```powershell
$env:PYTHONPATH="C:\GenAI Final Project"
streamlit run streamlit_app/streamlit_main.py
```
