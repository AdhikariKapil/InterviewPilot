import json
import uuid
from datetime import datetime
from typing import List, Optional

from database.supabase_client import supabase
from models.ielts_model import (
    IELTSGenerateResponse,
    IELTSSpeakingPart2,
    IELTSSpeakingQuestions,
)
from services.llm_service import LLMService
from utils.logger import get_logger

logger = get_logger("ielts_service")


class IELTSService:
    # IELTS speaking test generation and evaluation
    def __init__(self):
        self.llm = LLMService()

    async def generate_speaking_test(self, user_id: str) -> IELTSGenerateResponse:
        logger.info(f"Generating IELTS Speaking test for user: {user_id}")

        try:
            # Part 1
            part1_prompt = f"""
                Generate 5 simple introductory questions for IELTS Speaking Part 1.
                Topics should be common and everyday (hometown, work, studies, hobbies, weather, etc.).
                The questions should be short and direct.
                Please return only the questions, without any additional text.
                The questions are going to be read by a voice assistant so do not use '/' or '*' or any other special characters which might break the voice assistant.
                Return the questions formatted like this:
                    ["Question 1", "Question 2", "Question 3", "Question 4", "Question 5"]

                Thank you!
            """
            part1_questions = await self.llm.generate_questions(
                ielts_prompt=part1_prompt
            )
            if not isinstance(part1_questions, list):
                logger.error("Part 1 questions not returned as list")
                raise ValueError("Part 1 questions not returned as list")
            part1_questions = [str(q) for q in part1_questions][:6]  # cap at 6

            # Part 2
            part2_prompt = f"""
                Generate one IELTS Speaking Part 2 card.
                The card must contain:
                    - A topic (e.g., "Describe a memorable holiday")
                    - A prompt starting with "you should say:" followed by 3-4 bullet points
                    - A list of bullet points (each as a string)
                    
                    Please return only a JSON object with the following exact structure,
                    without any additional text:
                        {{
                            "topic": "Your topic here",
                            "prompt": "You should say: ...",
                            "bullet_points": ["point 1", "point 2", "point 3"]
                            }}
                    The voice assistant will read the prompt and bullet points aloud, so do not use '/' or '*'
                    or any other special characters. Use only plain text. Make the topic appropriate for a general audience.
                    
                    Thank you!
            """

            part2_response = await self.llm.generate_questions(
                ielts_prompt=part2_prompt
            )
            part2_text = (
                part2_response[0]
                if isinstance(part2_response, list)
                else part2_response
            )
            part2_data = json.loads(part2_text)

            # Extract the topic for Part 3
            part2_topic = part2_data["topic"]

            part2 = IELTSSpeakingPart2(
                topic=part2_topic,
                prompt=part2_data["prompt"],
                bullet_points=part2_data["bullet_points"],
            )

            # Part 3
            part3_prompt = f"""
                Genearte 5 follow-up discussion question for IELTS Speaking Part 3.
                These questions must be directly related to the following topic: "{part2_topic}"

                The questions should be more abstract and require longer, detailed answers.
                Please return only the questions, without any additional text.
                The questions are going to be read by voice assistant so do not use '/' or '*'
                or any other special characters which might break the voice assistant.

                Return the questions formatted like this:
                    ["Question 1", "Question 2", "Question 3", ...]

                    Thank you!
            """

            part3_questions = await self.llm.generate_questions(
                ielts_prompt=part3_prompt
            )
            if not isinstance(part3_questions, list):
                logger.error("Part 3 questions not returned as a list")
                raise ValueError("Part 3 questions not returned as a list")

            part3_questions = [str(q) for q in part3_questions][:6]

            # Assemble and save the test
            questions = IELTSSpeakingQuestions(
                part1=part1_questions, part2=part2, part3=part3_questions
            )

            assessment_id = uuid.uuid4()
            assessment_data = {
                "id": str(assessment_id),
                "user_id": user_id,
                "assessment_type": "ielts_speaking",
                "role": None,
                "level": None,
                "techstack": None,
                "config": {"parts": ["part1", "part2", "part3"]},
                "questions": questions.model_dump(),
                "status": "in_progress",
                "created_at": datetime.now().isoformat(),
                "finalized": False,
            }

            supabase.table("assessments").insert(assessment_data).execute()
            logger.info(f"Assessment saved with ID: {assessment_id}")

            return IELTSGenerateResponse(
                success=True,
                assessment_id=assessment_id,
                questions=questions,
                message="IELTS Speaking test generated successfully",
            )

        except Exception as error:
            logger.error(
                f"Failed to generate IELTS Speaking test: {error}", exc_info=True
            )
            raise
