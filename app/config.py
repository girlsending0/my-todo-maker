from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_chat_id: int = 0
    webhook_url: str = ""
    timezone: str = "Asia/Seoul"
    anthropic_api_key: str = ""
    db_path: str = "todos.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
