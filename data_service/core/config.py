import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Application configuration settings.
    Loads values from environment variables defined in .env or Docker environment.
    """

    APP_NAME: str = "Smart Travel Data Service"

    # Connection string for MongoDB (Cloud Atlas)
    # Defaults to localhost if the environment variable is not set
    MONGODB_URI: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    
    # The name of the database to use
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "smart_travel_agent_db")

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()