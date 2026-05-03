# GenAI Final Project

## Project Goal

This repository contains a Streamlit proof of concept for an SMS-style recruiting chatbot for a Python Developer role. The assignment target is a main agent that decides whether to `continue`, `schedule`, or `end`, supported by three advisor agents plus external data sources.

For the detailed phase tracker and remaining scope, see `workplan.md`.

## Assignment Alignment Snapshot

Implemented now:
- Streamlit intake form captures candidate name and role before chat starts.
- Main-agent routing exists in `app/modules/agent_router.py` and delegates to exit, schedule, or info advisors.
- All three advisors use LangChain plus OpenAI structured outputs.
- Shared history is passed through the backend turn contract.
- SQL availability lookup is role-aware, limited to the nearest 3 slots, formatted into human-readable suggestions, and supports candidate-proposed times with exact-slot confirmation or nearest alternatives.
- Exit flow coverage now includes clear exit, clear continue, and ambiguous loopback cases through the final main-agent flow.
- Candidate-proposed time handling is implemented and covered by direct schedule-advisor tests plus conversation-service coverage.
- Backend smoke execution works through `app.main`.

Still missing or not assignment-aligned:
- The info advisor does not yet ingest the job-description PDF or retrieve grounded facts from Chroma.
- `sms_conversations.json` is not yet used for evaluation.
- No `test_evals.ipynb`, accuracy/confusion-matrix pipeline, or exit-advisor fine-tuning artifacts are in the repo.
- The Streamlit UI currently allows the role to be changed after intake, which weakens the Mermaid flow's fixed-known-role assumption.

## Current Verification

Latest checks on 2026-05-03:
- `app.main` passed.
- `tests/Code testing/test_conversation_service.py` passed with 19 tests.
- `tests/Code testing/test_exit_flow.py` passed.
- `tests/Code testing/test_agent_router.py` passed.

## Current Architecture

- `app/modules/conversation_service.py` builds the shared turn contract and calls the main agent.
- `app/modules/agent_router.py` is the main agent. It chooses one advisor per pass, supports loopback, and returns the final action plus reply.
- `app/modules/exit_advisor.py` decides whether the conversation should end.
- `app/modules/schedule_advisor.py` decides whether scheduling is appropriate, interprets candidate-proposed times against the seeded SQL calendar, and fetches exact or nearest slots from SQL.
- `app/modules/info_advisor.py` answers role/process questions, but it is currently prompt-only and not retrieval-backed.
- `streamlit_app/streamlit_main.py` provides the proof-of-concept UI.

## Data Sources

- `Database/db_Tech.sql`
	- Used today for schedule lookup.
	- Queried through a normalized-role path for schedule suggestions.
- `Database/sms_conversations.json`
	- Present in the repo.
	- Not yet consumed by an evaluation script or notebook.
- `Database/Job descriptions/Python Developer Job Description.pdf`
	- Present in the repo.
	- Not yet ingested into prompts, embeddings, or Chroma retrieval.

## Environment

Use a local `.env` file with this shape:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_CHAT_MODEL=gpt-4o-mini
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
SQL_SERVER_CONNECTION_STRING=your_sql_server_connection_string
CHROMA_PERSIST_DIR=./chroma_db
```

The `.env` file itself is ignored by Git.

## Local Setup

From the repo root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run Locally

Smoke-check the backend:

```powershell
.\.venv\Scripts\python.exe -m app.main
```

Run the Streamlit demo:

```powershell
$env:PYTHONPATH="C:\GenAI Final Project"
streamlit run streamlit_app/streamlit_main.py
```

## Testing

Run the current conversation-service suite:

```powershell
.\.venv\Scripts\python.exe -m unittest "tests/Code testing/test_conversation_service.py"
```

Run the exit-flow suite:

```powershell
.\.venv\Scripts\python.exe -m unittest "tests/Code testing/test_exit_flow.py"
```

Run the router integration suite:

```powershell
.\.venv\Scripts\python.exe -m unittest "tests/Code testing/test_agent_router.py"
```

Notes:
- `test_conversation_service.py` exercises the live LangChain/OpenAI plus SQL-backed path.
- `test_agent_router.py` and `test_exit_flow.py` are focused router-flow tests that mock the LLM boundary to verify orchestration behavior cheaply.

## Project Status

- The core multi-agent flow is implemented and working in Streamlit.
- Scheduling is SQL-backed, role-aware, and supports candidate-proposed times with exact-slot confirmation or nearest alternatives.
- The info advisor is currently prompt-only and not yet retrieval-backed.
- Evaluation, the required notebook, and fine-tuning are not implemented yet.

## Project Structure

- `app/` - backend entry point, config loader, and advisor orchestration modules
- `streamlit_app/` - Streamlit proof-of-concept frontend
- `Database/` - SQL seed script, labeled SMS conversations, and the job-description PDF
- `Docs/` - assignment material and flow reference
- `tests/` - current verification artifacts and unit tests
