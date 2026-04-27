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

## Current Baseline

- Environment/config loading works.
- SQL availability lookup works.
- Rule-based router exists for `continue`, `schedule`, and `end`.
- Streamlit single-turn demo works.
- `conversation_service.py` packages a single turn result.
- First unit test exists for the service layer.

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

## Slices

### Phase 1: Lock The Baseline Architecture
Status: `Done`

1. `Done` Align `app/main.py` with `conversation_service.py` so the backend smoke flow matches Streamlit.
2. `Done` Add a tiny shared conversation-turn input/output contract that can later carry history cleanly.
3. `Done` Make the main flow explicitly call exit, schedule, and info advisors in one place.
4. `Done` Add role tracking to conversation state so the system knows which role the candidate is discussing.
5. `Done` Normalize role names between conversation text and SQL positions, for example `Python Developer` to `Python Dev`.
6. `Done` Add one test for advisor precedence when a message could match more than one action.
7. `Done` Add one test for a neutral follow-up that should stay on `continue`.

### Phase 2: Make The Streamlit Demo Actually Conversational
Status: `Done`

1. `Done` Add `st.session_state` chat history so the demo is multi-turn instead of one-shot.
2. `Done` Display the conversation as recruiter/candidate turns rather than raw field output only.
3. `Done` Pass recent conversation history into `process_candidate_turn()`.
4. `Done` Make the backend meaningfully consume passed conversation history, not just carry UI state through the turn contract.
5. `Done` Add one test for a follow-up turn that depends on previous context after backend history consumption exists.

### Phase 3: First Real Info Advisor With OpenAI
Status: `In Progress`

1. `Done` Create a small LangChain/OpenAI integration slice for the info advisor only.
2. `TBD` Load the job description content as the source of truth for role-related answers.
3. `Done` Replace the rule-based info advisor with an OpenAI-backed answer generator.
4. `Done` Add prompt instructions so the info advisor answers role questions and gently drives toward scheduling.
5. `Done` Add a few few-shot examples for common candidate questions.
6. `Done` Make the main agent still return `continue` while the info advisor generates the response text.
7. `Done` Add a smoke test or verification note for a real role-question answer from the OpenAI-backed info advisor.
8. `Done` Add a shared recent-history prompt formatter so all advisors can receive consistent conversation context.
9. `Done` Update the info advisor to use shared conversation history for contextual follow-up questions.

### Phase 4: Strengthen The Exit Advisor
Status: `TBD`

1. `TBD` Replace the exit advisor keyword rule with an OpenAI-backed exit decision prompt.
2. `TBD` Add examples for disinterest, polite rejection, and ambiguous cases.
3. `TBD` Keep a lightweight fallback rule for obvious stop/bye/not-interested messages.
4. `TBD` Add tests for clear exit, clear continue, and ambiguous phrasing.

### Phase 5: Strengthen The Scheduling Advisor
Status: `TBD`

1. `TBD` Replace the current schedule keyword rule with a better scheduling decision prompt.
2. `TBD` Make the scheduling advisor use the detected role before querying SQL.
3. `TBD` Filter SQL availability by `position` so the candidate is matched to the correct role slots.
4. `TBD` Return only the nearest 3 available slots from SQL, matching the assignment wording.
5. `TBD` Format slots into human-readable strings for the demo.
6. `TBD` Add tests that schedule responses contain at most 3 suggested slots.
7. `TBD` Add one verification case where a scheduling-type message reaches the SQL-backed path.

### Phase 6: Candidate-Proposed Time Handling
Status: `TBD`

1. `TBD` Add a small parser or extraction step for candidate-proposed time phrases like `Friday at 11` or `next Monday`.
2. `TBD` Interpret proposed times relative to the conversation date when possible.
3. `TBD` Check whether the proposed slot exists in SQL for the detected role.
4. `TBD` If the slot exists, confirm it.
5. `TBD` If the slot does not exist, return the nearest 3 alternatives for that role.
6. `TBD` Add tests for requested-time available and requested-time unavailable cases.

### Phase 7: Job Description Ingestion
Status: `TBD`

1. `TBD` Locate and load the Python job description PDF or source material used for role answers.
2. `TBD` Add a one-time script/module to extract text from the document.
3. `TBD` Save the extracted content in a reusable form for embeddings and debugging.
4. `TBD` Add a quick verification step that the extracted text is readable and complete enough.

### Phase 8: Offline Embeddings And Chroma
Status: `TBD`

1. `TBD` Create the offline embedding slice using OpenAI embeddings.
2. `TBD` Store the embedded chunks in Chroma using the configured persist directory.
3. `TBD` Add chunking logic appropriate for a single job description document.
4. `TBD` Add a verification script that builds the Chroma collection successfully.
5. `TBD` Document how to rerun the embedding step locally.

### Phase 9: Retrieval-Augmented Info Advisor
Status: `TBD`

1. `TBD` Add a retrieval step from Chroma for role-related candidate questions.
2. `TBD` Feed retrieved context into the info advisor prompt.
3. `TBD` Compare the pre-RAG info answers with the retrieval-backed answers.
4. `TBD` Tune chunking/retrieval settings if answers are weak or hallucinated.
5. `TBD` Add a couple of verification cases for retrieval-backed job-detail questions.

### Phase 10: Main Agent Via LangChain Structure
Status: `TBD`

1. `TBD` Refactor the current router so it looks like a real main agent orchestrating the three advisors.
2. `TBD` Decide whether the main agent itself is LLM-driven or rule-plus-advisor driven for the scoped project.
3. `TBD` If using LangChain orchestration, make the advisor calls explicit and traceable.
4. `TBD` Ensure the main agent’s final action is still always one of `continue`, `schedule`, or `end`.
5. `TBD` Ensure the main agent keeps role context available to the scheduling path.
6. `TBD` Add one end-to-end verification case for each action.

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

1. `TBD` Improve the Streamlit layout so it feels like a recruiter chat demo, not a raw debug page.
2. `TBD` Show assistant replies in a cleaner chat format.
3. `TBD` Show scheduling suggestions clearly, including role-aware slot suggestions.
4. `TBD` Add a way to reset the conversation.
5. `TBD` Make sure the demo works for `continue`, `schedule`, and `end` flows.

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

- Phase 2: `Done` Own `st.session_state`, chat rendering, and the frontend side of passing history.
- Phase 3: `TBD` Own job-description loading, prompt wording, and info-answer shaping.
- Phase 6: `TBD` Own time-expression parsing and confirmation wording.
- Phase 9: `TBD` Own retrieval prompt integration and answer comparison.
- Phase 12: `TBD` Own the required evaluation notebook.
- Phase 14: `TBD` Own Streamlit polish and conversation UX.

### Worker B: Routing, Data, And Evaluation Track

- Phase 2: `Done` Own backend history consumption and the follow-up test coverage.
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
1. Real OpenAI-backed info advisor.
2. Role detection and normalization for scheduling.
3. Better scheduling advisor with nearest 3 SQL slots.
4. Multi-turn Streamlit chat history.
5. Offline embeddings into Chroma.
6. Retrieval-backed info answers.
7. Evaluation pipeline with accuracy and confusion matrix.
8. README cleanup.

## Suggested Next Slice

The best next slice from the current state is:

1. Create the first real OpenAI-backed info advisor.

Reason:
- it starts the actual GenAI part of the project
- it is smaller than full scheduling-time parsing
- it moves the project away from pure stubs quickly
- it gives a visible improvement in the Streamlit demo