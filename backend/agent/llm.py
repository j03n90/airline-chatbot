from langchain_openai import ChatOpenAI

from backend.config import settings


def openai_compatible_base_url(base_url: str) -> str:
    url = base_url.rstrip("/")
    if url.endswith("/v1"):
        return url
    return url + "/v1"


def chat_model() -> ChatOpenAI | None:
    if not settings.api_key:
        return None
    return ChatOpenAI(
        model=settings.model,
        api_key=settings.api_key,
        base_url=openai_compatible_base_url(settings.base_url),
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
