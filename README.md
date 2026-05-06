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
- Router and advisor prompts/examples are aligned around the assignment labels: default toward `schedule`, use `continue` for genuine role or screening follow-up questions, and use `end` for clear stop signals or confirmed interview slots.
- Eval replay passes each JSON turn's `timestamp_utc` into the backend so relative date phrases are interpreted against the dataset time; live/demo scheduling still falls back to the seeded SQL calendar reference date.
- Exit flow coverage now includes clear exit, clear continue, and ambiguous loopback cases through the final main-agent flow.
- Candidate-proposed time handling is implemented and covered by direct schedule-advisor tests plus conversation-service coverage.
- `tests/test_evals.ipynb` evaluates the router against `Database/sms_conversations.json` and saves local row-level CSV output under `tests/eval*.csv` files, which are ignored by Git.
- Backend smoke execution works through `app.main`.

Still missing or not assignment-aligned:
- The info advisor does not yet ingest the job-description PDF or retrieve grounded facts from Chroma.
- Exit-advisor fine-tuning artifacts are not in the repo.
- The Streamlit UI currently allows the role to be changed after intake, which weakens the Mermaid flow's fixed-known-role assumption.

## Current Verification

Latest checks on 2026-05-06:
- Prompt/advisor syntax check passed with `py_compile`.
- `tests/test_evals.ipynb` executed on 44 candidate-turn examples.
- Baseline eval from commit `191339d`: label accuracy `18/44` = `0.409`.
- Best prompt/advisor-alignment eval: label accuracy `35/44` = `0.795`.
- Final `gpt-4o-mini` prompt-tuning eval: label accuracy `34/44` = `0.773`; schedule-slot match on correctly labeled schedule rows `4/17` = `0.235`.
- Changing the chat model from `gpt-4o-mini` to `gpt-5.4-mini-2026-03-17` improved label accuracy to `39/44` = `0.886`; schedule-slot match was `4/19` = `0.211`.

The largest improvement came from aligning the schedule, info, exit, and synthesis prompts with the router policy. The schedule advisor now supports the selected scheduling path instead of vetoing qualification answers back to `continue`.

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
	- Used by `tests/test_evals.ipynb` for router label accuracy, confusion matrix, and schedule-slot comparison.
- `Database/Job descriptions/Python Developer Job Description.pdf`
	- Present in the repo.
	- Not yet ingested into prompts, embeddings, or Chroma retrieval.

## Environment

Use a local `.env` file with this shape:

```env
OPENAI_API_KEY=your_openai_key
OPENAI_CHAT_MODEL=gpt-5.4-mini-2026-03-17
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

Run the dataset eval notebook:

```powershell
.\.venv\Scripts\python.exe -m ipykernel install --user --name genai-final-project --display-name "GenAI Final Project"
.\.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute tests/test_evals.ipynb --output test_evals.ipynb --ExecutePreprocessor.timeout=1800 --ExecutePreprocessor.kernel_name=genai-final-project
```

Notes:
- `test_conversation_service.py` exercises the live LangChain/OpenAI plus SQL-backed path.
- `test_agent_router.py` and `test_exit_flow.py` are focused router-flow tests that mock the LLM boundary to verify orchestration behavior cheaply.
- `test_evals.ipynb` exercises the live backend and may take several minutes because it calls the LLM-backed router/advisors for each dataset row.

## Project Status

- The core multi-agent flow is implemented and working in Streamlit.
- Scheduling is SQL-backed, role-aware, and supports candidate-proposed times with exact-slot confirmation or nearest alternatives.
- The info advisor is currently prompt-only and not yet retrieval-backed.
- The required evaluation notebook is implemented; fine-tuning is not implemented yet.

## Project Structure

- `app/` - backend entry point, config loader, and advisor orchestration modules
- `streamlit_app/` - Streamlit proof-of-concept frontend
- `Database/` - SQL seed script, labeled SMS conversations, and the job-description PDF
- `Docs/` - assignment material and flow reference
- `tests/` - current verification artifacts and unit tests
