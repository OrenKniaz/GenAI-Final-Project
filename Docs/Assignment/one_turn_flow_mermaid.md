# One-Turn Conversation Flow

This file is the implementation reference for the assignment-aligned one-turn flow.

Key interpretation choices:
- The candidate starts from an intake/registration form before the chat begins.
- The role should be known at chat start, preferably from a dropdown or controlled input.
- The main agent orchestrates every turn.
- Advisors return structured feedback to the main agent.
- The main agent synthesizes advisor outputs into the final user-facing action and response.
- The main agent may consult one or more advisors again if the first pass is not sufficient.

```mermaid
flowchart TD
    A([Start]) --> B[Fill registration form]
    B --> C[Capture known role and candidate details]
    C --> D[Start conversation with known role in state]
    D --> E[User sends current message]

    E --> F[Main Agent receives current message]
    F --> G[Build shared turn context]
    G --> G1[Known role]
    G --> G2[Full chat history]
    G --> G3[Current message]
    G --> G4[Conversation time metadata]

    G --> H[Consult Exit Advisor]
    G --> I[Consult Info Advisor]
    G --> J[Consult Scheduling Advisor]

    H --> H1[Return exit feedback]
    H1 --> H2[exit_match true or false]
    H1 --> H3[optional rationale]

    I --> I1[Determine whether more role info is needed]
    I1 --> I2[If needed, retrieve role facts from job description or vector store]
    I2 --> I3[Return info feedback]
    I3 --> I4[info_needed true or false]
    I3 --> I5[optional candidate-facing info reply]
    I3 --> I6[optional rationale]

    J --> J1[Determine whether scheduling is appropriate]
    J1 --> J2[If needed, retrieve SQL availability for the known role]
    J2 --> J3[Return scheduling feedback]
    J3 --> J4[schedule_match true or false]
    J3 --> J5[optional slot suggestions]
    J3 --> J6[optional rationale]

    H2 --> K[Main Agent synthesizes advisor outputs]
    I4 --> K
    I5 --> K
    J4 --> K
    J5 --> K

    K --> L{Enough information to answer this turn?}
    L -->|No| M[Main Agent asks one or more advisors again with clarified guidance]
    M --> H
    M --> I
    M --> J
    L -->|Yes| N{Final action}

    N -->|end| O[Respond politely and end conversation]
    N -->|schedule| P[Respond with scheduling message and slot suggestions]
    N -->|continue| Q[Respond with info or follow-up message]

    O --> R([Turn complete])
    P --> R
    Q --> R
```

## Expected Responsibilities

- Main Agent:
  - owns the turn loop
  - owns advisor orchestration
  - owns the final action decision
  - owns the final candidate-facing response
- Exit Advisor:
  - returns whether the conversation should end
- Info Advisor:
  - returns whether more role information is needed and the supporting reply content
- Scheduling Advisor:
  - returns whether it is time to schedule and the supporting slot suggestions

## Important Implementation Notes

- The role should not primarily be inferred from free text once the intake form exists.
- Advisors should consume shared context rather than maintain separate state models.
- SQL scheduling must be role-aware.
- Job-description facts should come from the PDF or the retrieval layer once added.
- The main agent should remain the only component that decides the final turn action shown to the user.
