import os

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from utils.secrets import get_secure_secret

load_dotenv()


class Settings(BaseSettings):
    """Application settings with validation"""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    # Required settings
    bot_token: str

    # Database settings
    database_url: str = "sqlite+aiosqlite:///./deadlines.sqlite"

    # Scheduler settings
    scheduler_timezone: str = "UTC"
    notification_check_interval: int = 1  # minutes
    upcoming_check_interval: int = 1  # minutes

    # Rate limiting settings
    rate_limit_time_window: int = 10  # seconds
    rate_limit_max_calls: int = 5

    # Logging settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Security settings
    max_title_length: int = 200
    max_description_length: int = 1000
    max_deadline_title_length: int = 200
    max_deadline_description_length: int = 1000

    # Notification settings
    default_notification_enabled: bool = True
    default_notification_advance_hours: int = 24
    max_notification_advance_hours: int = 168  # 1 week

    # Environment
    environment: str = "development"
    debug: bool = False


def load_settings():
    """Load settings with proper error handling"""
    # Determine environment
    env = os.getenv("ENVIRONMENT", "development").lower()

    # Load environment-specific .env file
    env_files = []
    if env == "production":
        env_files.append(".env.production")
    elif env == "development":
        env_files.append(".env.development")
    env_files.append(".env")  # Fallback to default

    # Try to load each environment file
    for env_file in env_files:
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            print(f"Loaded configuration from {env_file}")
            break

    try:
        # Try to get bot token from secure storage first
        bot_token = get_secure_secret("BOT_TOKEN")
        if not bot_token:
            bot_token = os.getenv("BOT_TOKEN", "")

        settings = Settings(bot_token=bot_token)
        if not settings.bot_token:
            raise ValueError("BOT_TOKEN is required")
        return settings
    except Exception as e:
        print(f"Configuration error: {e}")
        print(f"Please check your .env files (tried: {', '.join(env_files)})")
        print("Ensure BOT_TOKEN is set")
        exit(1)


# Backwards compatibility
settings = load_settings()
BOT_TOKEN = settings.bot_token
SQL_URL = settings.database_url
