import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Initialize singleton Google Gemini LLM instance
llm_instance = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=settings.google_api_key,
    temperature=0.7,
)


def get_llm() -> ChatGoogleGenerativeAI:
    """Returns the configured LLM instance for agent and summarizer execution."""
    return llm_instance
