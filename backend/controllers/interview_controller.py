import uuid
from datetime import datetime

from fastapi import HTTPException, Request

from database.supabase_client import supabase
from models.interview_model import GenerateRequest, GenerateResponse
from services.ip_tracking import IPTrackingService
from services.llm_service import LLMService
from services.subscription_service import SubscriptionService
from utils.logger import get_logger

logger = get_logger("interview_controller")


async def handle_generate_interview(
    request: Request, data: GenerateRequest
) -> GenerateResponse:
    client = request.client

    if client is None:
        logger.warning("Request has no client info")
        client_ip = "unknown"
    else:
        client_ip = client.host
        logger.info(f"Generate request from IP: {client_ip}, user: {data.userid}")

    ip_service = IPTrackingService()
    subscription_service = SubscriptionService()

    can_access_free = ip_service.can_access_free_tier(client_ip)

    if not can_access_free:
        has_subscription = subscription_service.has_active_subscription(
            data.userid, "core_interview"
        )
        if not has_subscription:
            raise HTTPException(
                status_code=403,
                detail="Free limit reached. Please subscribe to continue.",
            )
        logger.info(f"User {data.userid} accessed via subscription")
    else:
        logger.info(f"User {data.userid} accessed via free tier")

        # Generate questions

    try:
        llm_service = LLMService()
        questions = await llm_service.generate_questions(
            role=data.role,
            level=data.level,
            type=data.type,
            techstack=data.techstack,
            amount=data.amount,
        )
        logger.info(f"Question Generated: {questions}")
    except Exception as error:
        logger.error(f"LLM Questions generation failed: {error}")
        raise HTTPException(status_code=500, detail="Failed to generate quesitons")

    # Save to Subabase
    assessment_id = str(uuid.uuid4())
    techstack_array = [t.strip() for t in data.techstack.split(",") if t.strip()]

    try:
        assessment_data = {
            "id": assessment_id,
            "userid": data.userid,
            "assessment_type": "job_interview",
            "role": data.role,
            "level": data.level,
            "techstack": techstack_array,
            "questions": questions,
            "status": "in_progress",
            "created_at": datetime.now().isoformat(),
            "finalized": False,
        }

        supabase.table("assessments").insert(assessment_data).execute()
        logger.info(f"Assessment Saved: {assessment_id}")

        if can_access_free:
            ip_service.increment_ip_count(client_ip)
            logger.info(f"Increment IP count for {client_ip}")
    except Exception as error:
        logger.error(f"Failed to save assessment: {error}")
        raise HTTPException(status_code=500, detail="Failed to save assessment")

    return GenerateResponse(
        success=True,
        assessment_id=assessment_id,
        message="Interview generated successfully",
    )
