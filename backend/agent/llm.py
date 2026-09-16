from langchain_openai import ChatOpenAI

from backend.config import settings


def chat_model() -> ChatOpenAI | None:
    if not settings.deepseek_api_key:
        return None
    return ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url.rstrip("/") + "/v1",
        temperature=0,
    )


def complete(system: str, user: str) -> str:
    model = chat_model()
    if model is None:
        return ""
    result = model.invoke(
        [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
    )
    return str(result.content or "").strip()
