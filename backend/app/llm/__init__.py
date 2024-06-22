from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
import os


class ModelNames(Enum):
    GPT4_O = "gpt-4o"
    GPT4_TURBO = "gpt-4-turbo-2024-04-09"
    GPT3_TURBO = "gpt-3.5-turbo-0125"
    LLAMA70 = "llama3-70b-8192"
    CLAUDE_OPUS = "claude-3-opus-20240229"


class LLMInitializer:
    def __init__(self, model_name: str, temperature: float = 0.3):
        self.model_name = model_name
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if temperature < 0.0 or temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        self.temperature = temperature
        self.llm = None
        if not (self.openai_api_key or self.groq_api_key or self.anthropic_api_key):
            raise ValueError("API key not found")
        self.initialize_model()

    def initialize_model(self):
        if self.openai_api_key and self.model_name in [
            ModelNames.GPT3_TURBO.value,
            ModelNames.GPT4_TURBO.value,
            ModelNames.GPT4_O.value,
        ]:
            self.llm = ChatOpenAI(
                model=self.model_name,
                api_key=self.openai_api_key,
                temperature=self.temperature,
            )
        elif self.groq_api_key and self.model_name in [
            ModelNames.LLAMA70.value,
        ]:
            self.llm = ChatGroq(
                api_key=self.groq_api_key,
                model=self.model_name,
                temperature=self.temperature,
            )
        elif self.anthropic_api_key and self.model_name == ModelNames.CLAUDE_OPUS.value:
            self.llm = ChatAnthropic(
                timeout=60,
                model=self.model_name,
                api_key=self.anthropic_api_key,
                temperature=self.temperature,
            )
        else:
            raise ValueError("The model name is not supported")

    def get_llm(self):
        if self.llm is None:
            raise AttributeError("LLM not initialized properly")
        return self.llm
