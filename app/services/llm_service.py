import os
import logging
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def get_llm() -> ChatGroq:
    """
    Returns a Groq LLM instance. Called lazily inside each agent
    so the API key is always loaded from .env before first use.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY is not set. "
            "Add it to your .env file before running the app."
        )

    return ChatGroq(
        model="llama-3.1-8b-instant",
        temperature=0.3,
        streaming=True,
    )