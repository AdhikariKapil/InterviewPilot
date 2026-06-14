import json
import os
from abc import ABC, abstractmethod
from typing import List, Optional

import httpx
from g4f.client import Client
from g4f.Provider import DeepSeek

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
                    questions_from_split = [
                        q.strip() for q in question_text.split("\n") if q.strip()
                    ]
                    logger.info(f"QUESTIONS: {questions_from_split}")
                    return questions_from_split
        except Exception as error:
            logger.error(f"DeepSeek generation failed: {error}")
            raise


class GroqLLM(BaseLLM):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_questions(self, prompt: str) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "llama3-8b-8192",  # or "mixtral-8x7b-3276"
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.7,
                    },
                )
                if response.status_code != 200:
                    logger.error(f"Groq API Error: {response.text}")
                    raise Exception("Groq API error")

                response_json = response.json()
                question_text = response_json["choices"][0]["message"]["content"]

                try:
                    questions = json.loads(question_text)
                    if not isinstance(questions, list):
                        logger.error("Response from AI model is not a list")
                        raise ValueError("Response is not list")
                    return questions
                except:
                    logger.warning("Falied to parse JSON, falling back to line split")
                    return [q.strip() for q in question_text.split("\n") if q.strip()]
        except Exception as error:
            logger.error(f"Groq generation failed: {error}")
            raise


class GeminiLLM(BaseLLM):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_questions(self, prompt: str) -> List[str]:
        models_to_try = [
            "gemini-2.0-flash",
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-1.0-pro",
        ]
        last_error = None

        for model in models_to_try:
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}",
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                    )
                    if response.status_code == 200:
                        response_json = response.json()
                        question_text = response_json["candidates"][0]["content"][
                            "parts"
                        ][0]["text"]

                        try:
                            questions = json.loads(question_text)
                            if not isinstance(questions, list):
                                raise ValueError("Response is not list")
                            return questions
                        except:
                            return [
                                q.strip()
                                for q in question_text.split("\n")
                                if q.strip()
                            ]
                    else:
                        logger.warning(f"Gemini model {model} failed: {response.text}")
                        last_error = response.text
            except Exception as error:
                logger.error(f"Gemini generation failed: {error}")
                last_error = str(error)
        logger.error(f"All Gemini models failed. Last error: {last_error}")
        raise Exception(f"Gemini API error: {last_error}")


class G4FLLM(BaseLLM):
    async def generate_questions(self, prompt: str) -> List[str]:
        try:
            client = Client()

            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                provider=DeepSeek,
            )
            question_text = response.choices[0].message.content

            try:
                questions = json.loads(question_text)
                if not isinstance(questions, list):
                    logger.error("Response from AI model is not a list")
                    raise ValueError("Response is not list")
                return questions
            except:
                logger.warning("Failed to parse JSON, falling back to line split")
                return [q.strip() for q in question_text.split("\n") if q.strip()]
        except Exception as error:
            logger.error(f"g4f generation failed: {error}")
            raise


class HuggingFaceLLM(BaseLLM):
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def generate_questions(self, prompt: str) -> List[str]:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://router.huggingface.co/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "messages": [{"role": "user", "content": prompt}],
                        "model": "openai/gpt-oss-120b:fastest",
                        "stream": False,
                        "temperature": 0.7,
                    },
                )
                if response.status_code != 200:
                    logger.error(f"HuggingFace API error: {response.text}")
                    raise Exception(f"HuggingFace API error: {response.text}")

                response_json = response.json()
                question_text = response_json["choices"][0]["message"]["content"]

                try:
                    questions = json.loads(question_text)
                    if not isinstance(questions, list):
                        raise ValueError("Response is not list")
                    return questions
                except:
                    return [q.strip() for q in question_text.split("\n") if q.strip()]

        except Exception as error:
            logger.error(f"HuggingFace generation failed: {error}")
            raise


class LLMService:
    # Facotry service for LLM providers.
    def __init__(self):
        self.provider = os.getenv("LLM_PROVIDER", "gemini").lower()

        if self.provider == "g4f":
            logger.info(f"LLM provider {self.provider} used (no API key required).")
            self._llm = G4FLLM()
            logger.info(f"LLM provider initialized: {self.provider}")
            return

        api_key_name = f"{self.provider.upper()}_API_KEY"
        self.api_key = os.getenv(api_key_name)

        if not self.api_key:
            logger.error(f"{api_key_name} not set in environment")
            raise ValueError(f"{api_key_name} not set in environment")

        if self.provider == "deepseek":
            logger.info(f"LLM provider {self.provider} used.")
            self._llm = DeepseekLLM(self.api_key)
        elif self.provider == "gemini":
            logger.info(f"LLM provider {self.provider} used.")
            self._llm = GeminiLLM(self.api_key)
        elif self.provider == "groq":
            logger.info(f"LLM provider {self.provider} used.")
            self._llm = GroqLLM(self.api_key)
        elif self.provider == "huggingface":
            logger.info(f"LLM provider {self.provider} used.")
            self._llm = HuggingFaceLLM(self.api_key)

        else:
            logger.error(f"Unknown LLM provider: {self.provider}")
            raise ValueError(f"Unknown LLM provider: {self.provider}")

        logger.info(f"LLM provider initialized: {self.provider}")

    async def generate_questions(
        self,
        role: Optional[str] = None,
        level: Optional[str] = None,
        type: Optional[str] = None,
        techstack: Optional[str] = None,
        amount: Optional[int] = None,
        ielts_prompt: Optional[str] = None,
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

        if ielts_prompt:
            return await self._llm.generate_questions(ielts_prompt)
        else:
            return await self._llm.generate_questions(prompt)
