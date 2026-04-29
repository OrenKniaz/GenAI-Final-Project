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
- SQL availability lookup works.
- `conversation_service.py` packages a single turn result.
- Streamlit multi-turn chat state works.
- Shared conversation history formatting exists.
- An OpenAI-backed info advisor prototype exists and can use history.
- An OpenAI-backed router prototype exists, but it does not yet match the assignment's consult-all-advisors orchestration flow.
- An OpenAI-backed exit advisor prototype exists, but it is not yet fully integrated into the final main-agent loop.
- Streamlit now starts with an intake form that captures first name, last name, and role before chat begins.
- The backend still allows role changes from chat text during the conversation, so intake role is not yet the only source of truth.
- Unit tests exist for the service layer and current prototype routing behavior.

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
Status: `TBD`

1. `TBD` Define structured advisor outputs for exit feedback, info feedback, and scheduling feedback.
2. `TBD` Make the existing advisors return structured feedback instead of owning the final turn result directly.
3. `TBD` Keep the final action enum and final user-facing decision at the main-agent layer.
4. `TBD` Add one integration test showing that structured advisor outputs can be composed in a single turn.

### Phase 3: Info Advisor To Assignment Shape
Status: `In progress`

1. `Done` Create a small LangChain/OpenAI integration slice for the info advisor.
2. `Done` Add prompt instructions so the info advisor answers role questions and can guide the candidate toward scheduling.
3. `Done` Add a few few-shot examples for common candidate questions.
4. `Done` Make the info advisor consume shared conversation history for contextual follow-up questions.
5. `Done` Add a smoke test or verification note for a real role-question answer from the OpenAI-backed info advisor.
6. `TBD` Change the info advisor from a direct final responder into a structured advisor that returns `info_needed` plus draft reply content to the main agent.
7. `TBD` Load the job description content as the source of truth for supported role information.
8. `TBD` Add verification that supported role facts come from the job description pipeline rather than free-form model knowledge.

### Phase 4: Exit Advisor To Assignment Shape
Status: `In progress`

1. `Done` Replace the exit keyword rule with an OpenAI-backed exit confirmation prompt.
2. `Done` Add clear exit, clear continue, and ambiguous examples.
3. `Done` Make the exit advisor consume shared conversation history.
4. `TBD` Add a safe fallback when structured output is malformed or the model call fails.
5. `TBD` Integrate the exit advisor into the consult-all-advisors main-agent loop.
6. `TBD` Add tests for clear exit, clear continue, and ambiguous phrasing through the final main-agent flow.

### Phase 5: Scheduling Advisor To Assignment Shape
Status: `TBD`

1. `TBD` Create an OpenAI-backed scheduling advisor that returns `schedule_match` plus optional scheduling guidance.
2. `TBD` Make the scheduling advisor use the known role from intake state before it queries SQL.
3. `TBD` Filter SQL availability by `position` so the candidate is matched to the correct role slots.
4. `TBD` Return only the nearest 3 available slots from SQL, matching the assignment wording.
5. `TBD` Format slot suggestions into human-readable strings for the main agent to present.
6. `TBD` Add tests that scheduling feedback contains at most 3 suggested slots.
7. `TBD` Add one verification case where a scheduling-type turn reaches the SQL-backed scheduling advisor path.

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
Status: `TBD`

1. `TBD` Make the main agent own the full turn loop and the final action decision for every message.
2. `TBD` Make the main agent consult Exit, Info, and Scheduling advisors on every turn using shared context.
3. `TBD` Make advisor calls explicit and traceable in LangChain or the chosen orchestration layer.
4. `TBD` Make the main agent synthesize advisor outputs into the final `continue`, `schedule`, or `end` decision.
5. `TBD` Make the main agent own the final candidate-facing response, even when advisor draft content is used.
6. `TBD` Add a second-pass advisor consultation path when the first advisor outputs are insufficient or conflicting.
7. `TBD` Ensure the main agent can pass clarified reasoning when it consults advisors again.
8. `TBD` Add one end-to-end verification case for each final action.

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
Status: `TBD`

1. `TBD` Polish the intake form or dropdown so the known role capture feels like a natural chat entry step.
2. `TBD` Show assistant replies in a cleaner chat format.
3. `TBD` Show scheduling suggestions clearly, including role-aware slot suggestions.
4. `TBD` Add a way to reset the conversation.
5. `TBD` Make sure the demo works for `continue`, `schedule`, and `end` flows.
6. `TBD` Make sure the UI reflects main-agent orchestration rather than a single-advisor shortcut.

### Phase 15: README And Submission Quality
Status: `TBD`

1. `TBD` Rewrite the README around the actual final architecture.
2. `TBD` Add local setup instructions for config, SQL, embeddings, and Streamlit.
3. `TBD` Add basic usage examples for the demo flow.
4. `TBD` Document the project structure and what each major module does.
5. `TBD` Document how `sms_conversations.json`, SQL, and the job description are each used in the system.
6. `TBD` Document how evaluation is run and where outputs are stored.

### Phase 16: Final Verification And Packaging
Status: `TBD`

1. `TBD` Run backend smoke verification.
2. `TBD` Run Streamlit verification.
3. `TBD` Run unit tests.
4. `TBD` Run evaluation and confirm accuracy/confusion matrix outputs exist.
5. `TBD` Verify the role-aware scheduling path is using the correct SQL position field.
6. `TBD` Do a final repo cleanup pass to remove dead stubs and make the code consistent.

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

1. Add intake-form role capture so the conversation starts with a known role in state.

Reason:
- it matches the very start of the assignment diagram
- it removes avoidable role ambiguity before advisor orchestration becomes more complex
- it simplifies scheduling, retrieval, and testing because the role is known from the first turn
- it is a smaller and cleaner correction slice than full orchestration refactor