from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate

import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

class ModelNames(Enum):
    GPT4_O= "gpt-4o"
    GPT4_TURBO = "gpt-4-turbo-2024-04-09"
    GPT3_TURBO = "gpt-3.5-turbo-0125"
    LLAMA70 = "llama3-70b-8192"
    CLAUDE_OPUS = "claude-3-opus-20240229"

class LLMInitializer:
    def __init__(self,
                 model_name:str,
                 temperature:float = 0.3,
        ):
        self.model_name = model_name
        if temperature < 0.0 or temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        self.temperature = temperature
        self.initialize_model()

    def initialize_model(self):
        if "gpt" in self.model_name:
            if OPENAI_API_KEY and (self.model_name== "gpt-3.5-turbo-0125" or self.model_name== "gpt-4-turbo-2024-04-09" or self.model_name== "gpt-4o"):
                self.llm = ChatOpenAI(model_name=self.model_name, api_key=OPENAI_API_KEY, temperature=self.temperature)
        elif GROQ_API_KEY and (self.model_name=="llama3-70b-8192" or self.model_name=="llama3-8b-8192"):
            self.llm = ChatGroq(api_key=GROQ_API_KEY,model_name=self.model_name,temperature=self.temperature)
        elif ANTHROPIC_API_KEY and self.model_name=="claude-3-opus-20240229":
            self.llm = ChatAnthropic(api_key=ANTHROPIC_API_KEY,model_name=self.model_name,temperature=self.temperature)
        else:
            raise ValueError("The model name is not supported")
    
    def get_llm(self):
        return self.llm


if __name__ == "__main__":
    llm_init = LLMInitializer(model_name=ModelNames.GPT3_TURBO,temperature=0.3)
    llm = llm_init.get_llm()
    prompt = ChatPromptTemplate.from_messages(
        messages=[
            ("system","You are a stoic philosofer"),
            ("user","{input}"),
        ]
    )
    chain = prompt | llm
    result=chain.invoke({"input":"What is the meaning of life?"})
    print(result)