import os
from enum import Enum
from openai import OpenAI
from anthropic import Anthropic


class ModelNames(Enum):
    GPT4_O = "gpt-4o"
    GPT4_TURBO = "gpt-4-turbo-2024-04-09"
    GPT3_TURBO = "gpt-3.5-turbo-0125"
    CLAUDE_OPUS = "claude-3-opus-20240229"


class LLMInitializer:
    def __init__(self, model_name: str, temperature: float = 0.3):
        self.model_name = model_name
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if temperature < 0.0 or temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        self.temperature = temperature
        self.client = None
        if not (self.openai_api_key or self.anthropic_api_key):
            raise ValueError("API key not found")
        self.initialize_model()

    def initialize_model(self):
        if self.openai_api_key and self.model_name in [
            ModelNames.GPT3_TURBO.value,
            ModelNames.GPT4_TURBO.value,
            ModelNames.GPT4_O.value,
        ]:
            self.client = OpenAI(api_key=self.openai_api_key)
        elif self.anthropic_api_key and self.model_name == ModelNames.CLAUDE_OPUS.value:
            self.client = Anthropic(api_key=self.anthropic_api_key)
        else:
            raise ValueError("The model name is not supported")

    def get_completion(self, messages):
        if isinstance(self.client, OpenAI):
            response = self.client.chat.completions.create(
                model=self.model_name, messages=messages, temperature=self.temperature
            )
            return response.choices[0].message.content
        elif isinstance(self.client, Anthropic):
            # Convert messages to Anthropic format
            anthropic_messages = [
                {
                    "role": "human" if msg["role"] == "user" else "assistant",
                    "content": msg["content"],
                }
                for msg in messages
            ]
            response = self.client.messages.create(
                model=self.model_name,
                messages=anthropic_messages,
                max_tokens=2000,
                temperature=self.temperature,
            )
            return response.content
        else:
            raise ValueError("Client not properly initialized")
