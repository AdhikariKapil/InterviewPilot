import os

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from utils.logger import get_logger

logger = get_logger("auth_service")

security = HTTPBearer()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    # Validate the JWT and return the user_id
    token = credentials.credentials
    try:
        if not SUPABASE_JWT_SECRET:
            logger.error("SUPABASE_JWT_SECRET not set in environment")
            raise ValueError("SUPABASE_JWT_SECRET not set in environment")

        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audiencce="authenticated",
        )

        user_id = payload.get("sub")
        if not user_id:
            logger.error("JWT payload missing sub")
            raise HTTPException(status_code=401, detail="Invalid token")

        logger.info(f"Authenticated user: {user_id}")
        return user_id
    except jwt.ExpiredSignatureError as error:
        logger.warning("JWT expired")
        raise HTTPException(status_code=401, detail="Token expired")

    except jwt.InvalidTokenError as error:
        logger.error(f"Invalid token: {error}")
        raise HTTPException(status_code=401, detail="Invalid token")
