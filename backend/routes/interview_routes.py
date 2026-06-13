from fastapi import APIRouter, Depends, Request

from controllers.interview_controller import handle_generate_interview
from models.interview_model import GenerateRequest, GenerateResponse
from services.auth import get_current_user

router = APIRouter(prefix="/interview", tags=["Interview"])


@router.post("/generate", response_model=GenerateResponse)
async def generate_interview(
    request: Request, data: GenerateRequest, user_id: str = Depends(get_current_user)
):
    return await handle_generate_interview(request, data, user_id)
