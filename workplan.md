# Work Plan

## Status Legend

- `TBD`
- `In progress`
- `Done`

## Assignment Target

Build a Streamlit proof of concept of an SMS-style recruiting chatbot for a Python developer role.

The finished project should show:
- a main agent that decides `continue`, `schedule`, or `end`
- three advisor agents: exit, schedule, and info
- LangChain and OpenAI used as part of the agent architecture
- SQL-backed scheduling
- use of the labeled `sms_conversations.json` dataset for evaluation and model improvement
- use of the job description as the source of truth for role information
- offline embeddings from the job description into Chroma
- evaluation on the labeled conversation dataset with accuracy and confusion matrix
- a clean repo, README, and demo flow suitable for grading

## Project Data Sources

The project should use all three important data sources in the repo, not just the SQL database.

1. `Database/db_Tech.sql`
	The schedule table is not generic. It has a `position` column, so scheduling must match the candidate to the right role before proposing slots.

2. `Database/sms_conversations.json`
	This is not just sample data. It is the labeled dataset for evaluation, and it can also help with prompt examples, failure analysis, and fine-tuning preparation.

3. `Database/Job descriptions/Python Developer Job Description.pdf`
	This is the knowledge source for answering candidate questions about the role, and later for embeddings plus Chroma retrieval.

## Current Prototype Status

- Environment/config loading works.
- `conversation_service.py` is working and routes turns through `agent_router.run_turn()`.
- `agent_router.py` is the unified main agent and now runs again after fixing a blocking `_synthesize()` typo on 2026-04-29.
- The main agent routes one advisor per pass, synthesizes the final reply, and supports loopback up to 3 passes.
- All 3 advisors use LangChain/OpenAI structured outputs and accept `main_agent_note` for loopback.
- Exit advisor: wired and now covered by dedicated final-flow tests for clear exit, clear continue, and ambiguous loopback phrasing.
- Info advisor: wired with history and candidate-name context; prompt cleanup is complete, but job-description ingestion and retrieval-backed grounding are still future work.
- Schedule advisor: wired to SQL with role-aware filtering, returns the nearest 3 slots, formats human-readable suggestions, and carries a SQL-derived schedule reference date for the seeded calendar.
- Streamlit starts from an intake form and captures candidate name plus role before chat begins.
- Streamlit also allows changing the role from the sidebar after intake, which conflicts with the Mermaid flow's fixed known-role assumption.
- Shared conversation history formatting exists, but it is plain text only and does not include speaker labels or turn timestamps.
- `sms_conversations.json` is present in the repo but is not used by the app or an evaluator yet.
- The Python job description PDF is present in the repo and reserved for the later ingestion and retrieval phases.
- No Chroma build step, retrieval layer, evaluation notebook, or fine-tuning artifacts are present in the repo.
- Verification on 2026-04-30: `app.main` passes; `test_conversation_service.py` passes; `test_exit_flow.py` passes; `test_agent_router.py` passes.

## A+ Outcome

An A+ version of this project should feel like a real but scoped GenAI system, not just keyword rules wrapped in Streamlit.

It should demonstrate:
- modular advisor-based architecture
- real OpenAI-backed reasoning in the advisors
- retrieval-backed role answers from Chroma
- SQL-based interview slot validation and nearest-slot suggestions
- multi-turn conversation flow in Streamlit
- measurable evaluation results on the provided labeled data
- clear documentation of what was built and how it performs

## Reference Architecture

The implementation target should follow the assignment-aligned one-turn flow documented in:

- `Docs/Assignment/one_turn_flow_mermaid.md`

That reference flow takes precedence over earlier prototype assumptions when the two disagree.

## Slices

### Immediate Fixes (Blocking Or High-Risk)

1. `Done` Fix the blocking typo in `agent_router.py` (`return respone` → `return response`) so routed turns execute again.
2. `Done` Align the current tests with the known-role scheduling contract and stabilize the schedule-path assertions.
3. `Done` Align scheduling output with the assignment: role-filtered SQL, nearest 3 slots, and human-readable formatting.

### Phase 1: Shared Foundations And Known Role Setup
Status: `Done`

1. `Done` Align `app/main.py` with `conversation_service.py` so the backend smoke flow matches Streamlit.
2. `Done` Add a shared conversation-turn input/output contract that can carry message, role, and history.
3. `Done` Add `st.session_state` chat history so the demo is multi-turn instead of one-shot.
4. `Done` Pass recent conversation history through the backend turn contract.
5. `Done` Add a shared conversation-history formatter for advisor prompts.
6. `Done` Normalize role names between user-facing role text and SQL positions, for example `Python Developer` to `Python Dev`.
7. `Done` Start the conversation from an intake or registration form that captures the role before chat begins.
8. `Done` Replace role inference as the primary source of truth with known role state from the intake flow.

### Phase 2: Shared Advisor Feedback Contracts
Status: `Done`

1. `Done` Define structured advisor outputs for exit feedback, info feedback, and scheduling feedback.
2. `Done` Make the existing advisors return structured feedback instead of owning the final turn result directly.
3. `Done` Keep the final action enum and final user-facing reply at the main-agent layer.
4. `Done` Add one integration test showing that a single advisor feedback can be routed through the main agent to a final turn result.

### Phase 3: Info Advisor To Assignment Shape
Status: `Done`

1. `Done` Create a small LangChain/OpenAI integration slice for the info advisor.
2. `Done` Add prompt instructions so the info advisor answers role questions and can guide the candidate toward scheduling.
3. `Done` Add few-shot examples including info_needed=true, info_needed=false, and loopback cases.
4. `Done` Make the info advisor consume shared conversation history for contextual follow-up questions.
5. `Done` Add a smoke test or verification note for a real role-question answer from the OpenAI-backed info advisor.
6. `Done` Change the info advisor from a direct final responder into a structured advisor that returns `info_needed` plus draft reply content to the main agent.
7. `Done` Clean up duplicate system prompt lines and duplicate examples in info_advisor.py (minor).

### Phase 4: Exit Advisor To Assignment Shape
Status: `Done`

1. `Done` Replace the exit keyword rule with an OpenAI-backed exit confirmation prompt.
2. `Done` Add clear exit, clear continue, ambiguous, and loopback examples with rationale.
3. `Done` Make the exit advisor consume shared conversation history.
4. `Done` Integrate the exit advisor into the main-agent loop via agent_router.
5. `Done` Add tests for clear exit, clear continue, and ambiguous phrasing through the final main-agent flow.

### Phase 5: Scheduling Advisor To Assignment Shape
Status: `Done`

1. `Done` Create an OpenAI-backed scheduling advisor that returns `schedule_match` plus rationale.
2. `Done` Call `get_available_slots()` and attach slots to feedback when schedule_match is true.
3. `Done` Accept `main_agent_note` and support loopback examples.
4. `Done` Filter SQL availability by `position` so the candidate is matched to the correct role slots.
5. `Done` Return only the nearest 3 available slots from SQL, matching the assignment wording.
6. `Done` Format slot suggestions into human-readable strings (currently raw DB tuples).
7. `Done` Add tests that scheduling feedback contains at most 3 suggested slots.
8. `Done` Add one verification case where a scheduling-type turn reaches the SQL-backed scheduling advisor path.

### Phase 6: Candidate-Proposed Time Handling
Status: `TBD`

1. `TBD` Add a parser or extraction step for candidate-proposed time phrases like `Friday at 11` or `next Monday`.
2. `TBD` Interpret proposed times relative to the conversation timestamp when possible.
3. `TBD` Check whether the proposed slot exists in SQL for the known role.
4. `TBD` If the proposed slot exists, confirm it.
5. `TBD` If the proposed slot does not exist, return the nearest 3 alternatives for that role.
6. `TBD` Add tests for requested-time available and requested-time unavailable cases.

### Phase 7: Job Description Ingestion
Status: `TBD`

1. `TBD` Locate and load the Python job description PDF used for role answers.
2. `TBD` Add a one-time script or module to extract text from the document.
3. `TBD` Save the extracted content in a reusable form for debugging, prompting, and embeddings.
4. `TBD` Add a quick verification step that the extracted text is readable and complete enough.
5. `TBD` Verify the extracted job-description content is the text source intended for later prompting and retrieval.

### Phase 8: Offline Embeddings And Chroma
Status: `TBD`

1. `TBD` Create the offline embedding step using OpenAI embeddings.
2. `TBD` Store the embedded chunks in Chroma using the configured persist directory.
3. `TBD` Add chunking logic appropriate for a single job description document.
4. `TBD` Add a verification script that builds the Chroma collection successfully.
5. `TBD` Document how to rerun the embedding step locally.

### Phase 9: Retrieval-Augmented Info Advisor
Status: `TBD`

1. `TBD` Add a retrieval step from Chroma for role-related candidate questions.
2. `TBD` Feed retrieved context into the info advisor prompt.
3. `TBD` Compare pre-RAG info answers with retrieval-backed answers.
4. `TBD` Tune chunking and retrieval settings if answers are weak or hallucinated.
5. `TBD` Add verification cases for retrieval-backed job-detail questions.

### Phase 10: Main-Agent Orchestration And Re-Consult Loop
Status: `Done`

1. `Done` Make the main agent own the full turn loop and the final action decision for every message.
2. `Done` Make the main agent route to exactly one advisor per pass, chosen based on current message and context.
3. `Done` Make advisor calls explicit and traceable via agent_router._call_advisor.
4. `Done` Make the main agent use the single advisor feedback to decide the final `continue`, `schedule`, or `end` action.
5. `Done` Make the main agent own the final candidate-facing response, even when advisor draft content is used.
6. `Done` Add a loopback path where the main agent can route to another advisor with clarified context if not confident after the first pass.
7. `Done` Ensure the clarified context passed on loopback explains what additional input the main agent needs.
8. `Done` Add one end-to-end verification case for each final action.

### Phase 11: Dataset Evaluation Pipeline
Status: `TBD`

1. `TBD` Inspect `Database/sms_conversations.json` and define how one conversation turn maps to a model input.
2. `TBD` Build a small evaluator that runs the system over the labeled examples.
3. `TBD` Record predicted action vs. labeled action for every example.
4. `TBD` Compute overall accuracy.
5. `TBD` Compute a confusion matrix.
6. `TBD` Use difficult cases from the dataset as prompt examples or failure-analysis examples where appropriate.
7. `TBD` Save intermediate evaluation outputs in a clean, reusable form.

### Phase 12: Required Evaluation Notebook
Status: `TBD`

1. `TBD` Create `test_evals.ipynb` in the required test area.
2. `TBD` Load evaluation outputs into the notebook.
3. `TBD` Show accuracy numerically.
4. `TBD` Plot or display the confusion matrix.
5. `TBD` Add a short failure analysis section with a few representative misses from `sms_conversations.json`.

### Phase 13: Fine-Tuning Slice For Exit Advisor
Status: `TBD`

1. `TBD` Inspect the labeled data for exit-related examples.
2. `TBD` Create a training-ready subset or JSONL file for exit-advisor fine-tuning.
3. `TBD` Document the fine-tuning approach even if full training is not completed inside the repo.
4. `TBD` If feasible within time and credits, run a small fine-tuning experiment.
5. `TBD` Compare baseline exit performance vs. fine-tuned or prompt-only exit behavior.

### Phase 14: Streamlit Demo Polish
Status: `In progress`

1. `In progress` Polish the intake form or dropdown so the known role capture feels like a natural chat entry step.
2. `Done` Show assistant replies in a cleaner chat format.
3. `TBD` Show scheduling suggestions clearly, including role-aware slot suggestions.
4. `TBD` Add a way to reset the conversation.
5. `In progress` Make sure the demo works for `continue`, `schedule`, and `end` flows.
6. `In progress` Make sure the UI reflects main-agent orchestration rather than a single-advisor shortcut.

### Phase 15: README And Submission Quality
Status: `In progress`

1. `Done` Rewrite the README around the actual current architecture and assignment status.
2. `In progress` Add local setup instructions for config, SQL, embeddings, and Streamlit.
3. `Done` Add basic usage examples for the demo flow.
4. `Done` Document the project structure and what each major module does.
5. `Done` Document how `sms_conversations.json`, SQL, and the job description are each currently used or not yet used in the system.
6. `TBD` Document how evaluation is run and where outputs are stored.

### Phase 16: Final Verification And Packaging
Status: `In progress`

1. `Done` Run backend smoke verification.
2. `In progress` Run Streamlit verification.
3. `Done` Run the current unit suites (`test_conversation_service.py`, `test_exit_flow.py`, and `test_agent_router.py`) and confirm they pass.
4. `TBD` Run evaluation and confirm accuracy/confusion matrix outputs exist.
5. `TBD` Verify the role-aware scheduling path is using the correct SQL position field.
6. `In progress` Do a final repo cleanup pass to remove dead stubs and make the code consistent.

### Phase 17: Evals Comparison
Status: `TBD`

1. `TBD` Prompts without examples.
2. `TBD` Prompts with examples.
3. `TBD` Prompts with examples and after fine-tuning the model on the database.

## Parallel Branch Plan

Use two parallel workers after Phase 1. Each worker develops on a separate feature branch, and the branches merge back together only at the end of the current phase after both tracks pass their phase-level checks.

### Worker A: Conversation And UX Track

- Phase 2: `TBD` Own chat rendering and frontend alignment with the new main-agent orchestration flow.
- Phase 1: `TBD` Own intake-form role capture and known-role UX.
- Phase 3: `TBD` Own job-description loading, prompt wording, retrieval context, and info-answer shaping.
- Phase 6: `TBD` Own time-expression parsing and confirmation wording.
- Phase 9: `TBD` Own retrieval prompt integration and answer comparison.
- Phase 12: `TBD` Own the required evaluation notebook.
- Phase 14: `TBD` Own Streamlit polish and conversation UX.

### Worker B: Routing, Data, And Evaluation Track

- Phase 2: `TBD` Own structured advisor outputs and shared advisor-result contracts.
- Phase 4: `TBD` Own exit-advisor prompt, fallback behavior, and tests.
- Phase 5: `TBD` Own scheduling decision logic, role-aware SQL filtering, and slot formatting.
- Phase 7: `TBD` Own document extraction and reusable storage.
- Phase 8: `TBD` Own embeddings build, Chroma persistence, and verification.
- Phase 11: `TBD` Own the dataset evaluator and saved outputs.
- Phase 13: `TBD` Own fine-tuning prep and baseline comparison.

### End-Of-Phase Merge Rule

- Each worker branches from the same phase start point.
- Each worker stays inside their phase scope until their track is green.
- Merge Worker A into the shared integration branch.
- Merge Worker B into the shared integration branch.
- Run the full phase verification only after both merges land.
- Promote to `main` only after the phase integration branch is stable.

## If Time Gets Tight

The minimum slices that still align well with the assignment are:
1. Intake form with known role captured before chat starts.
2. Main agent that consults all three advisors and owns the final `continue` / `schedule` / `end` decision.
3. OpenAI-backed info advisor that can answer role questions and guide toward scheduling.
4. OpenAI-backed exit advisor that confirms end vs continue.
5. Scheduling advisor that uses role-aware SQL and returns the nearest 3 slots.
6. Evaluation pipeline with accuracy and confusion matrix.
7. README cleanup.

## Suggested Next Slice

The best next slice from the current state is:

1. Move into Phase 6 candidate-proposed time handling.

Reason:
- scheduling and exit-flow verification are now in place, so the next real gap is natural-language time handling
- candidate-proposed time handling is the next major assignment behavior that is still fully open