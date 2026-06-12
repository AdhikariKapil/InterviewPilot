from fastapi import APIRouter, Request

from controllers.interview_controller import handle_generate_interview
from models.interview_model import GenerateRequest, GenerateResponse

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_interview(request: Request, data: GenerateRequest):
    return await handle_generate_interview(request, data)
