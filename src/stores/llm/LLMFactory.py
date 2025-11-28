from helpers.config import Settings
from .utils import get_all_models, get_api_key

class LLMFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._registry = get_all_models()
       
    def create(self, provider: str):
        Provider = self._registry.get(provider)
        
        if not Provider:
            return None
        
        api_key = get_api_key(settings=self.settings, Provider=Provider)
        
        return Provider(
            api_key=api_key,
            base_url=self.settings.OPENAI_API_URL,
            default_input_max_characters=self.settings.DEFAULT_GENERATION_INPUT_MAX_CHARACTERS,
            default_generation_output_max_tokens=self.settings.DEFAULT_GENERATION_OUTPUT_MAX_TOKENS,
            default_generation_temperature=self.settings.DEFAULT_GENERATION_TEMPERATURE
        )
