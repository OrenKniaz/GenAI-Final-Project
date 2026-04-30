from pydantic import BaseModel

from app.modules.Helpers.history_helper import format_conversation_history
from app.modules.Helpers.llm_helper import build_chat_llm
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage



# class that creates a schema for the router Feedback.
class ExitAdvisorFeedback(BaseModel):
    exit_match: bool # the decision...
    rationale: str  # give main agent\router the reasoning behind...

def get_exit_feedback(
    message: str,
    role: str | None = None,
    history: list[str] | None = None,
    main_agent_note: str | None = None,
) -> ExitAdvisorFeedback:

    llm = build_chat_llm(temperature=0)
    structured_llm = llm.with_structured_output(ExitAdvisorFeedback)
    history_text = format_conversation_history(history or [])
    role_text = role or "the role"
    note_text = f"\nMain agent note: {main_agent_note}" if main_agent_note else ""

    messages = [
        SystemMessage(
            content=(
                    "You are an exit advisor for a recruiting workflow.\n"
                    "Decide whether the candidate's latest message means the conversation should end.\n"
                    "Set exit_match to true only when the candidate clearly wants to stop, opt out, reject the process, or end the conversation.\n"
                    "Set exit_match to false when the candidate is still engaged, asking questions, expressing interest, delaying politely, or may want to continue later.\n"
                    "Use the recent conversation history when helpful.\n"
                    "If the message is ambiguous, prefer false.\n"
                    "Always provide a short rationale explaining your decision.\n"
                    "A polite farewell like 'thanks, bye for now' does NOT mean exit — it is ambiguous; prefer false.\n"
            )
        ),

        HumanMessage(content="Role: Python Developer\nCandidate question: What does this role focus on?"),
        AIMessage(content='{"exit_match": false, "rationale": "Candidate asked a role question, clearly still engaged."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: I still have questions about the role."),
        AIMessage(content='{"exit_match": false, "rationale": "Candidate is seeking more information, conversation should continue."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: Maybe later, can you tell me more first?"),
        AIMessage(content='{"exit_match": false, "rationale": "Candidate expressed interest and a polite delay, not an exit."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: I'm interested but not ready yet."),
        AIMessage(content='{"exit_match": false, "rationale": "Candidate asked about scheduling later, not withdrawing."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: Not interested anymore, thanks."),
        AIMessage(content='{"exit_match": true, "rationale": "Candidate explicitly stated they are no longer interested."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: Please stop messaging me."),
        AIMessage(content='{"exit_match": true, "rationale": "Candidate directly asked to stop contact."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: Goodbye, remove me from the process."),
        AIMessage(content='{"exit_match": true, "rationale": "Candidate explicitly asked to be removed from the hiring process."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: Thanks, bye for now."),
        AIMessage(content='{"exit_match": false, "rationale": "Polite farewell but no explicit opt-out. Ambiguous — defaulting to false."}'),

        HumanMessage(content="Role: Python Developer\nCandidate question: I do not think this is for me."),
        AIMessage(content='{"exit_match": true, "rationale": "Candidate clearly expressed the role is not a fit for them."}'),
        # Ambiguous
        HumanMessage(content="Role: Python Developer\nCandidate question: I don't know, maybe..."),
        AIMessage(content='{"exit_match": false, "rationale": "Message is ambiguous, could be hesitation or disengagement. Defaulting to false."}'),

        # Loopback: main agent already flagged ambiguity
        HumanMessage(content=(
            "Role: Python Developer\n"
            "Conversation history: Candidate said 'I am not sure this is for me' in a previous message.\n"
            "Main agent note: Unclear whether candidate wants to end or just pause — please check history for intent.\n"
            "Candidate question: I don't know, maybe..."
        )),
        AIMessage(content='{"exit_match": true, "rationale": "Conversation history shows prior disengagement signals. Combined with ambiguous message, exit is likely."}'),
        HumanMessage(
            content=(
                f"Role: {role_text}\n"
                f"{history_text}\n"
                f"{note_text}\n"
                f"Candidate question: {message}"
            )
        ),
    ]
    response = structured_llm.invoke(messages)
    
    # make sure response is in expected format, if it's a dict, and missing the key, default to false.
    if isinstance(response, dict):
        return ExitAdvisorFeedback(
            exit_match=response.get("exit_match", False),
            rationale=response.get("rationale", ""),
        )
    return response


if __name__ == "__main__":
    examples = [
        "Bye, I am done.",
        "I am not interested anymore.",
        "I still have questions about the role.",
    ]

    for example in examples:
        print(example, "->", get_exit_feedback(example, role="Python Developer"))