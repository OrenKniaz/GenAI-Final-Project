# One-Turn Conversation Flow

This file is the implementation reference for the assignment-aligned one-turn flow.

Key interpretation choices:
- The candidate starts from an intake/registration form before the chat begins.
- The role should be known at chat start, preferably from a dropdown or controlled input.
- The main agent orchestrates every turn.
- The main agent routes to exactly one advisor per pass, chosen based on the current message and context.
- The chosen advisor returns structured feedback to the main agent.
- If the main agent is not confident after the first advisor response, it can loop back and route to another advisor, passing additional context explaining why it needs more input.
- The main agent owns the final action and the final candidate-facing response.

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

    G --> ROUTE{Decides 1 out of 3 options}

    ROUTE -->|Exit Advisor| H[Send context to Exit Advisor]
    ROUTE -->|Sched Advisor| J[Send context to Scheduling Advisor]
    ROUTE -->|Info Advisor| I[Send context to Info Advisor]

    H --> H1[Processes complete chat history]
    H1 --> H2{Decides 1 out of 2 options}
    H2 -->|End Conversation| H3[exit_match true]
    H2 -->|Don't End Conv| H4[exit_match false]
    H3 --> HOUT[Send output to Main Agent]
    H4 --> HOUT

    J --> J1[Processes complete chat history]
    J1 --> J2{Decides 1 out of 2 options}
    J2 -->|Sched| J3[Retrieve SQL schedule options for known role]
    J2 -->|Don't Sched| J4[schedule_match false]
    J3 --> J5[schedule_match true, slot suggestions]
    J5 --> JOUT[Send output to Main Agent]
    J4 --> JOUT

    I --> I1[Processes complete chat history]
    I1 --> I2{Decides 1 out of 2 options}
    I2 -->|Info Needed| I3[Vector Retrieve Info from job description]
    I2 -->|Info Not Needed| I4[info_needed false]
    I3 --> I5[info_needed true, draft reply with retrieved facts]
    I5 --> IOUT[Send output to Main Agent]
    I4 --> IOUT

    HOUT --> K[Main Agent receives advisor feedback]
    JOUT --> K
    IOUT --> K

    K --> L{Confident enough to reply?}
    L -->|No - needs more input| M[Main Agent routes to another advisor with clarified context]
    M --> ROUTE
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
  - decides which one advisor to consult each pass
  - can loop back and consult another advisor if not confident, passing extra context
  - owns the final action decision (`continue`, `schedule`, or `end`)
  - owns the final candidate-facing response
- Exit Advisor:
  - receives message + history, decides `exit_match` true or false
- Scheduling Advisor:
  - receives message + history, decides `schedule_match` true or false
  - if schedule_match, retrieves available slots from SQL filtered by known role
- Info Advisor:
  - receives message + history, decides `info_needed` true or false
  - if info_needed, retrieves relevant facts from job description vector store
  - returns a draft candidate-facing reply

## Important Implementation Notes

- The role should not be inferred from free text; it comes from the intake form.
- Advisors consume shared context (message + history + role) rather than maintaining separate state.
- SQL scheduling must be role-aware using the normalized role value.
- Job-description facts should come from the PDF or the retrieval layer once added.
- The main agent is the only component that decides and sends the final turn reply to the candidate.
- The loopback pass should include a clarification note from the main agent explaining what additional input it needs.
