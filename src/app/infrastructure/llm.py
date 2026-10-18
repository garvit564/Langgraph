from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import get_settings

settings = get_settings()

# Ek baar initialize ho gaya, memory me ready rahega:
llm_instance = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    google_api_key=settings.google_api_key,
    temperature=0.7,)


def get_llm() -> ChatGoogleGenerativeAI:
    return llm_instance