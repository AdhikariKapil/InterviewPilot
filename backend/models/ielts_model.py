from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from utils.logger import get_logger

logger = get_logger("ielts_model")


class IELTSGenerateRequest(BaseModel):
    pass  # No fields needed - generation is based on the authenticated user


class IELTSSubmitPartRequest(BaseModel):
    # Request to submit answers for a single part of the IELTS Speaking test.
    assessment_id: UUID = Field(
        ..., description="The unique identifier of the assessment"
    )
    part: Literal["part1", "part2", "part3"] = Field(
        ..., description="Which part of the speaking test is being submitted"
    )
    answers: List[str] = Field(
        ..., min_length=1, description="List of answers for this part"
    )

    @field_validator("answers")
    @classmethod
    def validate_answers(cls, v: List[str]) -> List[str]:
        if not v:
            logger.error("Answer list cannot be empty")
            raise ValueError("Answer list cannot be empty")

        for i, ans in enumerate(v):
            if not ans.strip():
                logger.error(f"Answer at index {i} is empty or whitespace only")
                raise ValueError(f"Answer at index {i} is empty or whitespace only")

        return [ans.strip() for ans in v]


class IELTSSubmitFullTestRequest(BaseModel):
    assessment_id: UUID = Field(..., description="ID of assessement")
    part1_answers: List[str] = Field(
        ..., min_length=1, description="Answers for Part 1"
    )
    part2_answer: str = Field(..., min_length=1, description="Answer for Part2")
    part3_answers: List[str] = Field(
        ..., min_length=1, description="Answers for Part 3"
    )

    @field_validator("part1_answers", "part3_answers")
    @classmethod
    def validate_multiple_answers(cls, v: List[str]) -> List[str]:
        if not v:
            logger.error("Answer list cannot be empty")
            raise ValueError("Answer list cannot be empty")

        for i, ans in enumerate(v):
            if not ans.strip():
                logger.error(f"Answer at index {i} is empty or whitespace only")
                raise ValueError(f"Answer at index {i} is empty or whitespace only")

        return [ans.strip() for ans in v]

    @field_validator("part2_answer")
    @classmethod
    def validate_single_answer(cls, v: str) -> str:
        if not v.strip():
            logger.error("Part 2 answer cannot be empty or whitespace only")
            raise ValueError("Part 2 answer cannot be empty or whitespace only")

        return v.strip()


class IELTSSpeakingPart2(BaseModel):
    # Structure for IELTS Speaking Part 2 task card.

    topic: str = Field(..., description="The main topic for Part 2")
    prompt: str = Field(..., description="The full prompt text with bullet points")
    bullet_points: List[str] = Field(..., description="List of bullet points")


class IELTSSpeakingQuestions(BaseModel):
    part1: List[str] = Field(..., description="List of introductory questions")
    part2: IELTSSpeakingPart2 = Field(
        ..., description="Part 2 task card with topic and prompts"
    )
    part3: List[str] = Field(..., description="List of follow-up discussion questions")


class IELTSGenerateResponse(BaseModel):
    success: bool = Field(..., description="Whether the generation succeeded")
    assessment_id: UUID = Field(
        ..., description="The unique identifier of the assessment"
    )
    questions: IELTSSpeakingQuestions = Field(
        ..., description="The generated speaking test questions"
    )
    message: Optional[str] = Field(None, description="Optional informational message")


class IELTSFeedbackCriteria(BaseModel):
    # Per-criterial IELTS band scores(0-9 scale)
    fluency: float = Field(..., ge=0, le=9, description="Fluency score")
    coherence: float = Field(..., ge=0, le=9, description="Coherence score")
    grammar: float = Field(
        ..., ge=0, le=9, description="Grammatical range and accuracy score"
    )
    vocabulary: float = Field(..., ge=0, le=9, description="Lexical resource score")
    pronunciation: Optional[float] = Field(
        None,
        ge=0,
        le=9,
        description="Pronunciation score - may be None if not evaluable from transcript",
    )


class IELTSSubmitPartResponse(BaseModel):
    success: bool = Field(..., description="Whether the submission was successful")
    feedback_id: UUID = Field(
        ..., description="The unique identifier of the feedback record"
    )
    band_score: float = Field(
        ..., ge=0, le=9, description="Overall band score for this part"
    )
    criteria: IELTSFeedbackCriteria = Field(
        ..., description="Detailed per-criterion scores"
    )
    strengths: List[str] = Field(..., description="List of strengths observed")
    areas_for_improvement: List[str] = Field(
        ..., description="List of areas for improvement"
    )
    comment: str = Field(..., description="Overall feedback comment")


class IELTSSubmitFullTestResponse(BaseModel):
    success: bool = Field(..., description="Whether the submission was successful")
    feedback_id: UUID = Field(
        ..., description="The unique identifier of the overall feedback"
    )
    overall_band_score: float = Field(..., ge=0, le=9, description="Overall band score")
    part1_feedback: IELTSSubmitPartResponse = Field(
        ..., description="Feedback for Part 1"
    )
    part2_feedback: IELTSSubmitPartResponse = Field(
        ..., description="Feedback for Part 2"
    )
    part3_feedback: IELTSSubmitPartResponse = Field(
        ..., description="Feedback for Part 3"
    )
