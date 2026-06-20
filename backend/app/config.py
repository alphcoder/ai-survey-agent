from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_survey"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    max_questions_per_survey: int = 20
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"


settings = Settings()
