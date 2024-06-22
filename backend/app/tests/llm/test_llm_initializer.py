import pytest
import os
from unittest.mock import patch
from app.llm import LLMInitializer, ModelNames


# Test the ModelNames enum
def test_model_names_enum():
    assert ModelNames.GPT4_O.value == "gpt-4o"
    assert ModelNames.GPT4_TURBO.value == "gpt-4-turbo-2024-04-09"
    assert ModelNames.GPT3_TURBO.value == "gpt-3.5-turbo-0125"
    assert ModelNames.LLAMA70.value == "llama3-70b-8192"
    assert ModelNames.CLAUDE_OPUS.value == "claude-3-opus-20240229"


def test_initialize_openai_model():
    initializer = LLMInitializer(model_name=ModelNames.GPT4_O.value)
    assert os.getenv("OPENAI_API_KEY") == "fake_openai_key"
    llm = initializer.get_llm()
    assert initializer.model_name == ModelNames.GPT4_O.value
    assert llm


def test_initialize_groq_model():
    initializer = LLMInitializer(model_name=ModelNames.LLAMA70.value)
    assert os.getenv("GROQ_API_KEY") == "fake_groq_key"
    llm = initializer.get_llm()
    assert initializer.model_name == ModelNames.LLAMA70.value
    assert llm


def test_initialize_anthropic_model():
    initializer = LLMInitializer(model_name=ModelNames.CLAUDE_OPUS.value)
    assert os.getenv("ANTHROPIC_API_KEY") == "fake_anthropic_key"
    llm = initializer.get_llm()
    assert initializer.model_name == ModelNames.CLAUDE_OPUS.value
    assert llm


def test_invalid_model_name():
    with pytest.raises(ValueError, match="The model name is not supported"):
        LLMInitializer(model_name="invalid_model_name")


def test_missing_api_key():
    with patch.dict("os.environ", {}, clear=True):
        with pytest.raises(ValueError, match="API key not found"):
            LLMInitializer(model_name=ModelNames.GPT4_O.value)


def test_invalid_temperature():
    with pytest.raises(ValueError):
        LLMInitializer(model_name=ModelNames.GPT3_TURBO.value, temperature=2.1)
    with pytest.raises(ValueError):
        LLMInitializer(model_name=ModelNames.GPT3_TURBO.value, temperature=-0.1)
