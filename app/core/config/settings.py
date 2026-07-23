from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    app_name: str = Field(default="Job AI Agent", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")
    
    # Database
    database_url: str = Field(default="sqlite:///./data/jobs.db", env="DATABASE_URL")
    
    # API Settings
    api_host: str = Field(default="127.0.0.1", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT")
    api_reload: bool = Field(default=False, env="API_RELOAD")
    
    # Streamlit Settings
    streamlit_host: str = Field(default="127.0.0.1", env="STREAMLIT_HOST")
    streamlit_port: int = Field(default=8501, env="STREAMLIT_PORT")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="./logs/app.log", env="LOG_FILE")
    
    # Scheduler
    scheduler_enabled: bool = Field(default=True, env="SCHEDULER_ENABLED")
    scheduler_timezone: str = Field(default="UTC", env="SCHEDULER_TIMEZONE")
    
    # AI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    ai_model: str = Field(default="gpt-3.5-turbo", env="AI_MODEL")
    groq_api_key: Optional[str] = Field(default=None, env="GROQ_API_KEY")
    groq_model: str = Field(default="llama-3.3-70b-versatile", env="GROQ_MODEL")
    
    # Job Fetching
    fetch_interval_hours: int = Field(default=6, env="FETCH_INTERVAL_HOURS")
    max_jobs_per_run: int = Field(default=50, env="MAX_JOBS_PER_RUN")
    
    # Telegram Bot (Future)
    telegram_bot_token: Optional[str] = Field(default=None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(default=None, env="TELEGRAM_CHAT_ID")

    # Instahyre Authentication
    instahyre_email: Optional[str] = Field(
        default=None,
        env="neeragrawal05@gmail.com"
    )

    instahyre_session_file: str = Field(
        default="sessions/instahyre_session.json",
        env="INSTAHYRE_SESSION_FILE"
    )
    
    # Playwright (Future)
    playwright_headless: bool = Field(default=True, env="PLAYWRIGHT_HEADLESS")
    playwright_timeout: int = Field(default=30000, env="PLAYWRIGHT_TIMEOUT")

    # Wellfound Authentication
    wellfound_email: Optional[str] = Field(default=None, env="WELLFOUND_EMAIL")
    wellfound_password: Optional[str] = Field(default=None, env="WELLFOUND_PASSWORD")
    wellfound_session_file: str = Field(default="sessions/wellfound_session.json", env="WELLFOUND_SESSION_FILE")
    
    # Job Automation
    max_jobs_per_day: int = Field(default=10, env="MAX_JOBS_PER_DAY")
    min_score_threshold: float = Field(default=45.0, env="MIN_SCORE_THRESHOLD")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"



# Global settings instance
settings = Settings()
