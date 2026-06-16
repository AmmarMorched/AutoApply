from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:1234@localhost:5432/jobautomation"
    groq_api_key: str = ""
    storage_path: str = "./generated_resumes"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()