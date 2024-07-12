import os
from openai import OpenAI
from anthropic import Anthropic
from sqlalchemy.sql.functions import user
from sqlmodel import Session, select
from dataclasses import dataclass

from app.core.db import engine
from app.models import LLMInfo, Users, LLMTransactions, LLMTransactionTypesEnum


@dataclass
class LLMTransactionSummary:
    text: str
    llm_id: int
    input_tokens: int
    input_pricing: float
    output_tokens: int
    output_pricing: float
    total_cost: float


class TransactionManager:
    def __init__(self, user_id: int):
        self.user_id = user_id

    def record_transaction(
        self,
        llm_transaction_data: LLMTransactionSummary,
        task_type: LLMTransactionTypesEnum,
        job_posting_id: int | None = None,
        comparison_id: int | None = None,
    ):
        with Session(engine) as session:
            llm_transaction = LLMTransactions(
                user_id=self.user_id,
                llm_id=llm_transaction_data.llm_id,
                task_name=task_type.value[1],
                job_posting_id=job_posting_id,
                comparison_id=comparison_id,
                input_pricing=llm_transaction_data.input_pricing,
                input_tokens=llm_transaction_data.input_tokens,
                output_pricing=llm_transaction_data.output_pricing,
                output_tokens=llm_transaction_data.output_tokens,
                total_cost=llm_transaction_data.total_cost,
            )
            session.add(llm_transaction)
            self.decrease_user_balance(llm_transaction_data.total_cost)
            session.commit()

    def decrease_user_balance(self, cost: float):
        with Session(engine) as session:
            user = session.exec(select(Users).where(Users.id == self.user_id)).first()
            if user:
                user.balance -= cost
                session.add(user)
                session.commit()


class LLMInitializer:
    def __init__(self, model_name: str, user_id: int, temperature: float = 0.3):
        statement = select(LLMInfo).where(LLMInfo.public_name == model_name)
        model_info = Session(engine).exec(statement).first()
        if not model_info:
            raise ValueError("Model name not valid")
        self.model_info = model_info
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if temperature < 0.0 or temperature > 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        self.temperature = temperature
        self.client = None
        self.initialize_model()
        self.user_id = user_id
        self.transaction_manager = TransactionManager(user_id)

    def initialize_model(self):
        if self.model_info.provider == "OpenAI":
            if not self.openai_api_key:
                raise ValueError("OpenAI API key not found")
            self.client = OpenAI(api_key=self.openai_api_key)
        elif self.model_info.provider == "Anthropic":
            if not self.anthropic_api_key:
                raise ValueError("Anthropic API key not found")
            self.client = Anthropic(api_key=self.anthropic_api_key)
        else:
            raise ValueError("Model provider not supported")

    def get_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        task_type: LLMTransactionTypesEnum,
        job_posting_id: int | None = None,
        comparison_id: int | None = None,
    ) -> LLMTransactionSummary:
        if isinstance(self.client, OpenAI):
            messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": system_prompt}],
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": user_prompt}],
                },
            ]

            response = self.client.chat.completions.create(
                model=self.model_info.api_name,
                messages=messages,  # type: ignore
                temperature=self.temperature,
            )

            transaction = LLMTransactionSummary(
                text=response.choices[0].message.content,  # type: ignore
                input_tokens=response.usage.prompt_tokens,  # type: ignore
                output_tokens=response.usage.completion_tokens,  # type:ignore
                input_pricing=self.model_info.input_pricing,
                output_pricing=self.model_info.output_pricing,
                llm_id=self.model_info.id,  # type: ignore
                total_cost=response.usage.prompt_tokens * self.model_info.input_pricing  # type: ignore
                + response.usage.completion_tokens * self.model_info.output_pricing,  # type: ignore
            )

        elif isinstance(self.client, Anthropic):
            messages = [
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]}
            ]
            response = self.client.messages.create(
                model=self.model_info.api_name,
                messages=messages,  # type: ignore
                max_tokens=2000,
                system=system_prompt,
                temperature=self.temperature,
            )
            transaction = LLMTransactionSummary(
                text=response.content[0].text,  # type: ignore
                llm_id=self.model_info.id,  # type: ignore
                input_tokens=response.usage.input_tokens,  # type: ignore
                output_tokens=response.usage.output_tokens,  # type:ignore
                input_pricing=self.model_info.input_pricing,
                output_pricing=self.model_info.output_pricing,
                total_cost=response.usage.input_tokens * self.model_info.input_pricing  # type: ignore
                + response.usage.output_tokens * self.model_info.output_pricing,  # type: ignore
            )
        else:
            raise ValueError("Model provider not supported")

        self.transaction_manager.record_transaction(
            transaction, task_type, job_posting_id, comparison_id
        )
        return transaction


if __name__ == "__main__":
    llm = LLMInitializer("CLAUDE_SONNET", user_id=1, temperature=0.3)
    print(
        llm.get_completion(
            system_prompt="You are an assistant",
            user_prompt="Hello How are you?",
            task_type=LLMTransactionTypesEnum.USER_CV_EXTRACTION,
        )
    )
