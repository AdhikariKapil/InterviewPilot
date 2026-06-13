import os

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from database.supabase_client import supabase
from utils.logger import get_logger

load_dotenv()

logger = get_logger("auth_service")
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:

    token = credentials.credentials

    if not token:
        logger.error("No token provided in Authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No authentication token provided",
        )

    try:
        user_response = supabase.auth.get_user(token)

        if not user_response:
            logger.error("Supabase auth.get_user returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication service unavailable",
            )

        if not hasattr(user_response, "user") or user_response.user is None:
            logger.error("Supabase auth response missing 'user' or user is None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token - user not found",
            )

        user_id = user_response.user.id

        if not user_id or not isinstance(user_id, str) or len(user_id.strip()) == 0:
            logger.error("Invalid user_id in auth response")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user identifier",
            )

        logger.info(
            "User authenticated successfully",
            extra={"user_id": user_id, "auth_method": "jwt"},
        )
        return user_id

    except Exception as error:
        logger.error(f"Authorization failed: {error}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
