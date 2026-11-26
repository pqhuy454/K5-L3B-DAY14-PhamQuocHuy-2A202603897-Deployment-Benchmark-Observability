"""
Config — 12-Factor: mọi cấu hình đọc từ biến môi trường.

Các biến: PORT, ENVIRONMENT, AGENT_API_KEY, REDIS_URL,
RATE_LIMIT_PER_MINUTE, DAILY_BUDGET_USD, LOG_LEVEL.
Không hard-code secret trong code; liệt kê đủ biến trong .env.example.
"""
import os
from dataclasses import dataclass, field


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


@dataclass
class Settings:
    port: int = field(default_factory=lambda: _env_int("PORT", 8000))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", ""))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))
    rate_limit_per_minute: int = field(default_factory=lambda: _env_int("RATE_LIMIT_PER_MINUTE", 10))
    daily_budget_usd: float = field(default_factory=lambda: float(os.getenv("DAILY_BUDGET_USD", "10.0")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


settings = Settings()
