from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import HumanMessagePromptTemplate,SystemMessagePromptTemplate,PromptTemplate
from langchain_core.messages import SystemMessage
from langchain_core.pydantic_v1 import BaseModel, Field, validator
from typing import List
from langchain_community.callbacks import get_openai_callback
import PyPDF2
import re
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")





class ModelNames(Enum):
    GPT4_TURBO = "gpt-4-turbo-2024-04-09"
    GPT3_TURBO = "gpt-3.5-turbo-0125"

class LLMInitializer:
    def __init__(self,
                 model_name:str,
                 temperature:float = 0.3,
                 api_key:str = OPENAI_API_KEY):
        self.api_key = api_key
        self.model_name = model_name
        if temperature < 0.0 or temperature > 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0")
        self.temperature = temperature
        self.initialize_model()

    def initialize_model(self):
        if "gpt" in self.model_name:
            if self.api_key and (self.model_name== "gpt-3.5-turbo-0125" or self.model_name== "gpt-4-turbo-2024-04-09"):
                self.llm = ChatOpenAI(model_name=self.model_name, api_key=self.api_key, temperature=self.temperature)
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