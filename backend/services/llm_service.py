import json
import os
from abc import ABC, abstractmethod
from typing import List

import httpx

from utils.logger import get_logger

logger = get_logger("llm_service")


class BaseLLM(ABC):
    # Abstract base class for LLM providers.
    @abstractmethod
    async def generate_questions(self, prompt: str) -> List[str]:
        pass


class DeepseekLLM(BaseLLM):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_questions(self, prompt: str) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "deepseek-chat",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                    },
                )

                if response.status_code != 200:
                    logger.error(f"DeepSeek API error: {response.text}")
                    raise Exception("Deepseek API error")

                response_json = response.json()
                question_text = response_json["choices"][0]["message"]["content"]

                try:
                    questions = json.loads(question_text)
                    if not isinstance(questions, list):
                        logger.error("Response(questions) from ai model is not list")
                        raise ValueError("Response is not list")
                    return questions
                except:
                    logger.warning(f"Failed to parse JSON, falling back to line split")
                    # Fallback: split by lines
                    return [q.strip() for q in question_text.split("\n") if q.stirp()]
        except Exception as error:
            logger.error(f"DeepSeek generation failed: {error}")
            raise


class LLMService:
    # Facotry service for LLM providers.
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "deepseek").lower()
        api_key_name = f"{self.provider.upper()}_API_KEY"
        self.api_key = os.getenv(api_key_name)

        if not self.api_key:
            logger.error(f"{api_key_name} not set in environment")
            raise ValueError(f"{api_key_name} not set in environment")

        if self.provider == "deepseek":
            logger.info(f"LLM provider {self.provider} used.")
            self._llm = DeepseekLLM(self.api_key)
        else:
            logger.error(f"Unknown LLM provider: {self.provider}")
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        logger.info(f"LLM provider initialized: {self.provider}")

    async def generate_questions(
        self, role: str, level: str, type: str, techstack: str, amount: int
    ) -> List[str]:
        prompt = f"""
        Prepare questions for a job interview.
        The job role is {role}.
        The job experience level is {level}.
        The tech stack is used in the job is {techstack}.
        The focus between behavioural and technical questions should be towards: {type}.
        The amount of the questions required is : {amount}.
        Please return only the questions, without any additional text.
        The questions are going to be read by voice assistant so do not use '/' or "*" or any other special characters which might break the voice assistant.
        Return the questions formatted like this:
            ["Question 1", "Question 2", "Question 3"]

        Thank you!
        """

        logger.info(f"Generated questions.")
        return await self._llm.generate_questions(prompt)
