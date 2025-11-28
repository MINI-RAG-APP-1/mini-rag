from helpers.config import Settings
from .LLMEnums import LLMEnums
from .providers import OpenAI, Cohere, Groq

def get_all_models() -> dict:
    providers_map = {
        LLMEnums.OPENAI.value: OpenAI,
        LLMEnums.COHERE.value: Cohere,
        LLMEnums.GROQ.value: Groq,
    }
    
    return providers_map

def get_api_key(settings: Settings, Provider):
    return {
        OpenAI: settings.OPENAI_API_KEY,
        Cohere:  settings.COHERE_API_KEY,
        Groq:    settings.GROQ_API_KEY,
    }.get(Provider)
