from langchain_openai import ChatOpenAI

from app.config import get_settings


def build_chat_llm(temperature: float = 0) -> ChatOpenAI:
    settings = get_settings()

    return ChatOpenAI(
        model=settings.openai_chat_model,
        api_key=settings.openai_api_key,
        temperature=temperature,
    )