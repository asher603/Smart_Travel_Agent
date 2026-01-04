import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application configuration settings.
    Loads values from environment variables defined in .env or Docker environment.
    """
    
    # --- הוספתי את השורה הזו שחסרה ---
    APP_NAME: str = "Smart Travel Data Service"

    # Connection string for MongoDB (Cloud Atlas)
    # Defaults to localhost if the environment variable is not set
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    
    # The name of the database to use
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "travel_db")

    class Config:
        case_sensitive = True
        # אופציונלי: טוען משתנים מקובץ .env אם מריצים לוקאלית (לא דרך דוקר)
        env_file = ".env"

settings = Settings()