from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:1234@localhost:5432/jobautomation"
    openai_api_key: str = ""
    serpapi_key: str = ""
    storage_path: str = "./generated_resumes"
    
    class Config:
        env_file = ".env"

settings = Settings()