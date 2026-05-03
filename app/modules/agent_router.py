from dataclasses import dataclass
from enum import Enum
from typing import Literal

from pydantic import BaseModel
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.modules.Helpers.history_helper import format_conversation_history
from app.modules.Helpers.llm_helper import build_chat_llm


# Shared input contract — built by conversation_service, passed to run_turn

@dataclass(frozen=True)
class TurnContext:
    message: str
    role: str | None
    history: list[str]
    first_name: str | None = None
    last_name: str | None = None
    main_agent_note: str | None = None  # empty on first pass; populated on loopback


# Internal routing types

class Action(str, Enum):
    CONTINUE = "continue"
    SCHEDULE = "schedule"
    END = "end"

# main agent decision contract for first loop after a turn. (context from user, not feedback from advisors) - choose the advisor schema.
class RouteSelection(BaseModel):
    action: Literal["continue", "schedule", "end"]


# Main agent output contract — returned to conversation_service (output to user after feedback synthesis)

class MainAgentDecision(BaseModel):
    action: Literal["continue", "schedule", "end"]
    reply: str
    confident: bool  # False triggers loopback to an advisor
    clarification_needed: str | None = None  # what the main agent needs on loopback
    slots: list[str] | None = None

# Step 1: decide which advisor to call

def _pick_advisor(context: TurnContext) -> Action:
    llm = build_chat_llm(temperature=0)
    structured_llm = llm.with_structured_output(RouteSelection)

    role_text = context.role or "the role"
    history_text = format_conversation_history(context.history)

    messages = [
        SystemMessage(content=(
            "You are a recruiting router for a hiring workflow.\n"
            "Classify the candidate's latest message into exactly one routing action.\n"
            "Use 'continue' for general conversation, role-information questions, or interest that does not request scheduling.\n"
            "Use 'schedule' when the candidate is trying to arrange an interview, asking about available times, or trying to book the next step.\n"
            "Use 'end' when the candidate clearly wants to stop or is no longer interested.\n"
            "If a message contains both scheduling language and a clear desire to stop, choose 'end'.\n"
            "If unsure, choose 'continue'."
        )),
        HumanMessage(content="Role: Python Developer\nCandidate question: What does this role focus on?"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: Do I need to know every framework already?"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: Not interested anymore, thanks"),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: I\'m interested"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: I\'m interested in interviewing for this role"),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: I\'m interested, but I still want to understand the role better"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: I\'m interested, goodbye"),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: Bye, can we schedule an interview?"),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: Can we set up an interview for next week?"),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: What times do you have available?"),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate question: This sounds good, but I have one more question first"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content=(
            f"Role: {role_text}\n"
            f"{history_text}\n"
            f"Candidate question: {context.message}"
        )),
    ]

    response = structured_llm.invoke(messages)
    decision_text = response.get("action", "continue") if isinstance(response, dict) else response.action # protection from dict reply instead of an object.

    if decision_text == "end":
        return Action.END
    if decision_text == "schedule":
        return Action.SCHEDULE
    return Action.CONTINUE

# Step 2: call the chosen advisor, get structured feedback

def _call_advisor(action: Action, context: TurnContext) -> tuple[str, list[str] | None]:
    # imported here to avoid circular imports at module load time
    from app.modules.exit_advisor import get_exit_feedback
    from app.modules.info_advisor import generate_info_feedback
    from app.modules.schedule_advisor import get_schedule_feedback

    if action == Action.END:
        fb = get_exit_feedback(context.message, context.role, context.history, context.main_agent_note)
        return f"Exit advisor: exit_match={fb.exit_match}, rationale={fb.rationale}", None

    if action == Action.SCHEDULE:
        fb = get_schedule_feedback(context.message, context.role, context.history, context.main_agent_note)
        slots = ", ".join(fb.slots) if fb.slots else "none"
        return (
            "Schedule advisor: "
            f"schedule_match={fb.schedule_match}, "
            f"reference_date={fb.reference_date_text}, "
            f"requested_time_text={fb.requested_time_text}, "
            f"requested_slot_text={fb.requested_slot_text}, "
            f"requested_slot_available={fb.requested_slot_available}, "
            f"rationale={fb.rationale}, "
            f"slots=[{slots}]"
        ), fb.slots

    fb = generate_info_feedback(
        context.message,
        context.role,
        context.history,
        context.first_name,
        context.last_name,
        context.main_agent_note,
    )
    return (
        f"Info advisor: info_needed={fb.info_needed}, "
        f"rationale={fb.rationale}, "
        f"draft_reply={fb.draft_reply}"
    ), None
# Step 3: synthesize advisor feedback into final reply

def _synthesize(context: TurnContext, feedback_summary: str) -> MainAgentDecision:
    llm = build_chat_llm(temperature=0.1)  # add a touch of temperature for more natural replies, while still being focused on the prompt guidance
    structured_llm = llm.with_structured_output(MainAgentDecision)

    history_text = format_conversation_history(context.history)
    candidate_name = context.first_name or "the candidate"

    response = structured_llm.invoke([
        SystemMessage(content=(
            "You are the main recruiting agent. You received structured feedback from one advisor.\n"
            "Decide the final action and write the final candidate-facing reply.\n"
            "Set confident to true if you have enough to reply clearly.\n"
            "When confident is false, populate clarification_needed with a specific question explaining what the advisor needs to resolve, e.g. 'Unclear whether candidate wants to end or just pause — please clarify intent.'\n"
            "Set confident to false only if the feedback is contradictory or clearly insufficient.\n"
            "Keep the reply brief and SMS-friendly (1-3 sentences). be polite and kind\n"
            "Do not mention advisors or internal routing to the candidate.\n"
            "Treat dates and times in schedule advisor feedback as authoritative seeded SQL calendar values. Do not reinterpret them using the real current date.\n"
        )),
        # Example: continue
        HumanMessage(content=(
            "Candidate name: Alex\n"
            "Role: Python Developer\n"
            "Conversation history: (none)\n"
            "Candidate message: What does this role focus on?\n"
            "Advisor feedback: Info advisor: info_needed=True, rationale=Candidate asked a direct role question, "
            "draft_reply=This role focuses on building Python-based software and collaborating with the team on development tasks."
        )),
        AIMessage(content=(
            '{"action": "continue", "reply": "Great question, Alex! This role focuses on building Python-based software '
            'and collaborating closely with the team. Happy to answer more or help you take the next step whenever you\'re ready.", '
            '"confident": true}'
        )),

        # Example: schedule
        HumanMessage(content=(
            "Candidate name: Jordan\n"
            "Role: Python Developer\n"
            "Conversation history: (none)\n"
            "Candidate message: Can we set up an interview?\n"
            "Advisor feedback: Schedule advisor: schedule_match=True, rationale=Candidate explicitly asked to set up an interview, "
            "slots=[Tuesday, 2024-01-02 at 09:00, Tuesday, 2024-01-02 at 11:00, Wednesday, 2024-01-03 at 14:00]"
        )),
        AIMessage(content=(
            '{"action": "schedule", "reply": "Absolutely, Jordan! Here are a few available slots: '
            'Tuesday, 2024-01-02 at 09:00, Tuesday, 2024-01-02 at 11:00, or Wednesday, 2024-01-03 at 14:00. '
            'Let me know which works best for you!", "confident": true}'
        )),

        # Example: end
        HumanMessage(content=(
            "Candidate name: Sam\n"
            "Role: Python Developer\n"
            "Conversation history: (none)\n"
            "Candidate message: I am not interested anymore, thanks.\n"
            "Advisor feedback: Exit advisor: exit_match=True, rationale=Candidate clearly stated they are no longer interested."
        )),
        AIMessage(content=(
            '{"action": "end", "reply": "Totally understood, Sam. Thanks so much for your time and best of luck with your search!", '
            '"confident": true}'
        )),
        # loopback example
        HumanMessage(content=(
            "Candidate name: Taylor\n"
            "Role: Python Developer\n"
            "Conversation history: (none)\n"
            "Candidate message: I don't know, maybe...\n"
            "Advisor feedback: Exit advisor: exit_match=False, rationale=Message is ambiguous, could be hesitation or disengagement."
        )),
        AIMessage(content=(
            '{"action": "continue", "reply": "", "confident": false, '
            '"clarification_needed": "Candidate message is ambiguous — unclear if they want to continue or exit. Please check conversation history for intent signals."}'
        )),
        HumanMessage(content=(
            f"Candidate name: {candidate_name}\n"
            f"Role: {context.role or 'the role'}\n"
            f"Conversation history:\n{history_text}\n"
            f"Candidate message: {context.message}\n"
            f"Advisor feedback: {feedback_summary}"
        )),
    ])

    if isinstance(response, dict):
        return MainAgentDecision(
            action=response.get("action", "continue"),
            reply=response.get("reply", ""),
            confident=response.get("confident", True),
            clarification_needed=response.get("clarification_needed"),
        )
    return response

# Public entry point — called by conversation_service

def run_turn(context: TurnContext, max_loops: int = 3) -> MainAgentDecision: # don't allow router agent to call advisors more than 3 times...
    for attempt in range(max_loops):
        action = _pick_advisor(context) # read prompts - > decide which advisor to call
        feedback_summary, slots = _call_advisor(action, context) - > call the advisor -> get his feedback
        decision = _synthesize(context, feedback_summary) # read feedback - > decide confidence level ->reply\loop to advisor with note if needed

        if decision.confident or attempt == max_loops - 1:
            return decision.model_copy(update={"slots": slots})

        # loopback: main agent re-enters with a note explaining what it needs
        context = TurnContext(
            message=context.message,
            role=context.role,
            history=context.history,
            first_name=context.first_name,
            last_name=context.last_name,
            main_agent_note=decision.clarification_needed or "Please provide more detail.",
        )
     # unreachable — only here to satisfy type checker if max_loops were ever 0
    raise RuntimeError("run_turn called with max_loops < 1")

if __name__ == "__main__":
    ctx = TurnContext(message="Can we schedule an interview?", role="Python Developer", history=[])
    print(run_turn(ctx))