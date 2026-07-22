from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    exchange_id: str = "binance"
    exchange_api_key: str = ""
    exchange_api_secret: str = ""
    use_testnet: bool = True

    # Telegram alerts (optional): if both are set, live runs push to your phone.
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


def load_settings() -> Settings:
    return Settings()
