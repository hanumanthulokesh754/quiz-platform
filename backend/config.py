import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

    JWT_SECRET = os.environ.get("JWT_SECRET", "dev-secret-change-me")
    JWT_EXPIRES_HOURS = int(os.environ.get("JWT_EXPIRES_HOURS", 24))

    FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "*")
