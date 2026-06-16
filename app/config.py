"""
HealthGuard AI — Centralized Configuration
All settings read from environment variables with sensible defaults for local dev.
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── Database ──────────────────────────────────────────────
    database_url: str = "sqlite:///./healthguard.db"

    # ── LLM Provider ─────────────────────────────────────────
    llm_provider: str = "fallback"  # "groq" or "fallback"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"

    # ── Target Application ───────────────────────────────────
    # Automatically point to the natively mounted TargetApp
    target_url: str = f"http://127.0.0.1:{os.getenv('PORT', '10000')}/target/api"

    # ── Server ───────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # ── Agent Thresholds ─────────────────────────────────────
    cpu_threshold: float = 50.0
    memory_threshold_mb: float = 100.0
    error_rate_threshold: float = 1.0
    latency_threshold_ms: float = 2000.0
    confidence_threshold: float = 0.8

    # ── Monitoring ───────────────────────────────────────────
    poll_interval_seconds: float = 2.0
    metrics_history_size: int = 50

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse comma-separated CORS origins into a list."""
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        # In production, also allow the Render/Vercel URLs
        render_url = os.environ.get("RENDER_EXTERNAL_URL")
        if render_url:
            origins.append(render_url)
        return origins

    @property
    def is_production(self) -> bool:
        """Detect if running on a cloud platform."""
        return bool(os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT"))



# Singleton instance
settings = Settings()
