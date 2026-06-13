from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


# Request Models
class GenerateRequest(BaseModel):
    role: str
    level: str
    type: str
    techstack: str
    amount: int


class AgentResponseRequest(BaseModel):
    text: str
    assessment_id: str


# Response Models
class GenerateResponse(BaseModel):
    success: bool
    assessment_id: str
    message: str = ""


class CategoryScore(BaseModel):
    name: str
    score: int
    comment: str


class FeedbackResponse(BaseModel):
    id: str
    assessment_id: str
    user_id: str
    total_score: float
    category_score: List[CategoryScore]
    strengths: List[str]
    areas_for_improvement: List[str]
    final_assessment: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# Database models (for reading from Supabase)
class Assessment(BaseModel):
    id: str
    user_id: str
    assessment_type: str  #'job_interview', 'ielts_speaking', 'ielts_writing'
    role: Optional[str] = None
    level: Optional[str] = None
    techstack: Optional[List[str]] = None
    questions: List[str]
    status: str = "in_progress"
    created_at: datetime
    finalized: bool = False


class Transcript(BaseModel):
    id: str
    assessment_id: str
    role: str  #'user' or 'assistant'
    content: str
    created_at: datetime
