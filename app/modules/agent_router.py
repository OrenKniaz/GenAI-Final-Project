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
    reference_datetime_utc: str | None = None

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
            "You are the routing policy for a recruiter.\n"
            "Return exactly one action: continue, schedule, or end.\n"
            "Route the next recruiter action. Do not write a friendly reply in your head and route from that tone.\n"
            "Decision order:\n"
            "1. end: choose only when the candidate clearly opts out, asks to stop, says they are not interested, or clearly accepts/confirms a concrete interview time in an active scheduling flow.\n"
            "2. continue: choose when the candidate asks a role-related question, or gives a weak/partial qualification answer that needs one more screening follow-up before scheduling.\n"
            "3. schedule: choose for everything else when the candidate is still engaged.\n"
            "Schedule is the default for ambiguous or non-question messages.\n"
            "Strong qualification answers, experience summaries, positive reactions, short acknowledgements, interest, readiness, and availability problems are schedule.\n"
            "Rejected or unavailable times are schedule unless the candidate clearly asks to stop or says they are not interested.\n"
            "If the candidate says they may follow up later because a proposed time is unavailable, still choose schedule unless there is an explicit stop signal.\n"
            "Phrases like 'I'll reach out later', 'I'll reconnect', 'I'll reach out if it becomes relevant', or 'if another time is relevant' are not end signals by themselves when the candidate is only rejecting a proposed time.\n"
            "Accepted or confirmed interview times are end, because the recruiter should close with confirmation.\n"
            "If there is any doubt between continue and schedule, choose schedule.\n"
        )),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: What does this role focus on day to day?"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: Is this remote, hybrid, or office based?"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: I am interested, but what technologies does the team use?"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: I have 3 years of experience, is that enough for this role?"),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter asked how long the candidate has used Python.\nCandidate prompt: I only have a few months of Python experience, but I am eager to learn quickly."),
        AIMessage(content='{"action": "continue"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: Not interested anymore, thanks"),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: Please stop contacting me."),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered Tuesday at 10:00 and Wednesday at 14:00.\nCandidate prompt: Tuesday at 10 works for me."),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered Wednesday at 10:00 or Thursday at 14:00.\nCandidate prompt: Wednesday at 10 AM works for me."),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter asked which interview time works best.\nCandidate prompt: Monday at 3 PM is good."),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered a morning interview slot.\nCandidate prompt: That time sounds good."),
        AIMessage(content='{"action": "end"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter asked what Python projects the candidate has built recently.\nCandidate prompt: I have several years of Python experience, mostly building internal tools and data services."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: I mostly build backend services in Python and SQL."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter asked about cloud experience.\nCandidate prompt: I have used AWS for small deployments, but not GCP yet."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: Yes, about three years of experience."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: Sounds interesting, I can handle it."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: That sounds fine."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nCandidate prompt: Can we set up an interview for next week?"),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered a few interview times.\nCandidate prompt: None of those times work for me."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered Thursday afternoon.\nCandidate prompt: Thursday is not good for me."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered an interview time.\nCandidate prompt: I am unavailable then because I have other commitments."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered Tuesday morning for an interview.\nCandidate prompt: I cannot do that time because I have another commitment. I can reconnect if another time is relevant."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered an interview slot.\nCandidate prompt: I am unavailable at that time, but I can reach out later if another option becomes relevant."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content="Role: Python Developer\nRecent conversation:\nRecruiter offered an interview slot.\nCandidate prompt: I am unavailable at that time because I have other commitments. I will reach out if it becomes relevant."),
        AIMessage(content='{"action": "schedule"}'),
        HumanMessage(content=(
            f"Role: {role_text}\n"
            f"{history_text}\n"
            f"Candidate prompt: {context.message}"
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
        fb = get_schedule_feedback(context.message, context.role, context.history, context.main_agent_note, context.reference_datetime_utc)
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
            "Write the final candidate-facing reply and keep the final action aligned with the advisor feedback.\n"
            "Main policy: prefer schedule unless it is 90% clear the candidate wants to end or asked a genuine information question.\n"
            "If advisor feedback starts with 'Schedule advisor' and schedule_match=True, set action to schedule and offer the provided slots.\n"
            "If advisor feedback starts with 'Exit advisor' and exit_match=True, set action to end and close kindly.\n"
            "If advisor feedback starts with 'Info advisor' and info_needed=True, set action to continue and answer the question.\n"
            "Do not turn a schedule advisor result with slots into a continue reply.\n"
            "Set confident to true if you have enough to reply clearly.\n"
            "When confident is false, populate clarification_needed with a specific question explaining what the advisor needs to resolve, e.g. 'Unclear whether candidate wants to end or just pause — please clarify intent.'\n"
            "Set confident to false only if the feedback is contradictory or clearly insufficient.\n"
            "Keep the reply brief and SMS-friendly (1-3 sentences). be polite and kind\n"
            "Do not mention advisors or internal routing to the candidate.\n"
            "Treat dates and times in schedule advisor feedback as authoritative seeded SQL calendar values. Do not reinterpret them using the real current date.\n"
            "When suggesting slots, especially when it is not clear between continue or schedule, be kind and mention that more information can be discussed during the interview.\n"
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
            'Let me know which works best for you! or if you need more options, I\'m here to help.", "confident": true}'
        )),

        HumanMessage(content=(
            "Candidate name: Riley\n"
            "Role: Python Developer\n"
            "Conversation history: Recruiter asked about Python project experience.\n"
            "Candidate message: I have several years of Python experience building internal data tools.\n"
            "Advisor feedback: Schedule advisor: schedule_match=True, reference_date=2024-01-02, "
            "requested_time_text=None, requested_slot_text=None, requested_slot_available=None, "
            "rationale=Candidate answered the screening question and stayed engaged, "
            "slots=[Wednesday, 2024-01-03 at 10:00, Thursday, 2024-01-04 at 14:00]"
        )),
        AIMessage(content=(
            '{"action": "schedule", "reply": "Thanks for sharing, Riley. Your Python experience sounds relevant, '
            'and more details can be discussed in the interview. The available slots are Wednesday, 2024-01-03 at 10:00 '
            'or Thursday, 2024-01-04 at 14:00. Which works best?", "confident": true}'
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

        HumanMessage(content=(
            "Candidate name: Casey\n"
            "Role: Python Developer\n"
            "Conversation history: Recruiter offered Tuesday at 10:00 or Wednesday at 14:00 for an interview.\n"
            "Candidate message: Tuesday at 10 works for me.\n"
            "Advisor feedback: Exit advisor: exit_match=True, rationale=Candidate accepted a specific proposed interview slot."
        )),
        AIMessage(content=(
            '{"action": "end", "reply": "Great, Casey. Tuesday at 10:00 is confirmed, and you will receive the calendar invite shortly.", '
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
        feedback_summary, slots = _call_advisor(action, context) # - > call the advisor -> get his feedback
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
            reference_datetime_utc=context.reference_datetime_utc,
            main_agent_note=decision.clarification_needed or "Please provide more detail.",
        )
     # unreachable — only here to satisfy type checker if max_loops were ever 0
    raise RuntimeError("run_turn called with max_loops < 1")

if __name__ == "__main__":
    ctx = TurnContext(message="Can we schedule an interview?", role="Python Developer", history=[])
    print(run_turn(ctx))
