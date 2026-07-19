import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME:str = "POC Application"
    OPENSEARCH_ADMIN_PASSWORD:str = os.getenv("OPENSEARCH_ADMIN_PASSWORD")
    INDICES:List[str] = ["users"]
    OPENSEARCH_URL:str = os.getenv("OPENSEARCH_URL", "https://localhost:9200")
    IS_PROD:Optional[bool] = os.getenv("IS_PROD", False)

    # Automatically read from a .env file
    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
