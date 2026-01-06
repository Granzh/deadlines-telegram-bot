import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI

from utils.health import get_health_checker
from db.session import create_engine_and_session
from config import settings

app = FastAPI(title="Deadlines Bot Health API", version="1.0.0")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring and Docker health checks"""
    try:
        # Initialize health checker with session factory if not already initialized
        checker = get_health_checker()
        if checker is None or checker.session_factory is None:
            _, session_factory = create_engine_and_session(settings.database_url)
            from utils.health import HealthCheckerManager

            HealthCheckerManager.initialize(session_factory)
            checker = get_health_checker()

        status = await checker.get_full_status()

        # Return appropriate HTTP status based on health
        http_status = 200 if status["status"] == "healthy" else 503

        return status, http_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }, 503


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Deadlines Telegram Bot",
        "status": "running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def run_health_server(port: int = 8000):
    """Run health check server in separate process"""
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    run_health_server()
