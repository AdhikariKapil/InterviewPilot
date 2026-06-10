import os

from dotenv import load_dotenv
from supabase import Client, create_client

from utils.logger import get_logger

logger = get_logger("database")

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL:
    logger.error("SUPABASE_URL is missing in .env file")
    raise ValueError("SUPABASE_URL is required but not set")

if not SUPABASE_KEY:
    logger.error("SUPABASE_KEY is missing in .env file")
    raise ValueError("SUPABASE_KEY is required but not set")

try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client initialized successfully")
except Exception as error:
    logger.error(f"Failed to initialize Supabase client: {error}")
    raise
