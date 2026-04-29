# temporary module to decide info action, to be turned agentic later.
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.modules.Helpers.llm_helper import build_chat_llm

from app.modules.Helpers.history_helper import format_conversation_history

# function to generate the info reponse based on message\role\history
def generate_info_response(
    message: str,
    role: str | None = None,
    history: list[str] | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> str:
    
    
    llm = build_chat_llm(temperature=0) # temp = 0 for determinstic response, stick to the job descritpion source.

    role_text = role or "the role"
    history_text = format_conversation_history(history or [])
    candidate_name = " ".join(part for part in [first_name, last_name] if part) or "the candidate"
    
    messages = [  # not only system\user, inclued also "few shot learning\promption"
        SystemMessage(
            content=(
                "You are a recruiting information advisor for a hiring workflow.\n"
                "Your job is to answer candidate questions about the role briefly and clearly.\n"
                "If the question is about the role, answer at a high level.\n"
                "Do not invent company-specific facts.\n"
                "If you are unsure, say you do not have confirmed details.\n"
                "When a candidate first name is provided, you may use it naturally for a light personal touch, but not in every sentence.\n"
                "When appropriate, gently encourage the candidate toward next steps such as scheduling."
        )
    ),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: What does this role focus on?"
        )
    ),
        AIMessage(
            content=(
                "This role focuses on building and maintaining Python-based software, "
                "working with technical systems, and collaborating with the team to solve development tasks. "
                "If you'd like, I can also help with next steps in the process."
        )
    ),

        HumanMessage(
            content=(
                "Role: Python Developer\n"
                "Candidate question: Do I need to know every framework already?"
        )
    ),
        AIMessage(
            content=(
                "Not necessarily every framework. Strong Python fundamentals and relevant development experience "
                "are usually the most important starting point. If you want, I can also help guide you toward scheduling."
        )
    ),

        HumanMessage(
            content=(
                f"Candidate: {candidate_name}\n"
                f"Role: {role_text}\n"
                f"{history_text}\n"
                f"Candidate question: {message}"
        )
    ),
    ]

    response = llm.invoke(messages)
    if isinstance(response.content, str):
        return response.content

    return str(response.content)


if __name__ == "__main__":
    question = "Can you tell me more about the Python Developer role?"
    print(generate_info_response(question, role="Python Developer"))