"""Shared LLM access point.

All agents must summarize/reason through this module rather than
instantiating their own LangChain client, so the model/base-url/timeout
config lives in exactly one place.
"""

from functools import lru_cache

from langchain_ollama import ChatOllama

from backend.app.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatOllama:
    return ChatOllama(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        temperature=0.1,
    )


def summarize(prompt: str) -> str:
    """Send a single-turn prompt to the local LLM and return plain text."""
    llm = get_llm()
    response = llm.invoke(prompt)
    return response.content if hasattr(response, "content") else str(response)
