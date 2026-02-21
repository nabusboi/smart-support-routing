"""
Configuration settings for Smart-Support Ticket Routing Engine
"""
import os
from typing import Optional
from pydantic import BaseModel


class Settings(BaseModel):
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = True
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    # ML Model Settings
    TRANSFORMER_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Urgency Settings
    HIGH_URGENCY_THRESHOLD: float = 0.8
    CIRCUIT_BREAKER_THRESHOLD_MS: int = 500
    
    # Deduplication Settings
    SIMILARITY_THRESHOLD: float = 0.9
    DUPLICATE_TIME_WINDOW_MINUTES: int = 5
    DUPLICATE_COUNT_THRESHOLD: int = 10
    
    # Webhook Settings
    SLACK_WEBHOOK_URL: Optional[str] = os.getenv("SLACK_WEBHOOK_URL")
    DISCORD_WEBHOOK_URL: Optional[str] = os.getenv("DISCORD_WEBHOOK_URL")


settings = Settings()
