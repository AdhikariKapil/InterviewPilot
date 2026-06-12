from fastapi import FastAPI

from routes.interview_routes import router as interview_router
from utils.logger import get_logger

logger = get_logger("main")

app = FastAPI(title="InterviewPilot", version="1.0.0")

app.include_router(interview_router)


@app.get("/")
async def root():
    logger.info("Root endpoint called")
    return {"message": "InterviewPilot API is running"}
