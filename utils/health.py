import logging
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import text

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health check service for monitoring bot status"""

    def __init__(self, session_factory=None):
        self.session_factory = session_factory
        self.startup_time = datetime.now(timezone.utc)

    async def check_database(self) -> Dict[str, Any]:
        """Check database connectivity"""
        try:
            if self.session_factory is None:
                # Create temporary session for health check
                from config import settings
                from db.session import create_engine_and_session

                _, session_factory = create_engine_and_session(settings.database_url)
                self.session_factory = session_factory

            async with self.session_factory() as session:
                _ = await session.execute(text("SELECT 1"))
                return {
                    "status": "healthy",
                    "response": "Database connection successful",
                }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def check_scheduler(self) -> Dict[str, Any]:
        """Check scheduler status"""
        try:
            from scheduler import get_scheduler_instance

            scheduler = get_scheduler_instance()

            if scheduler and scheduler.running:
                jobs = scheduler.get_jobs()
                return {
                    "status": "healthy",
                    "jobs_count": len(jobs),
                    "scheduler_running": True,
                }
            else:
                return {"status": "unhealthy", "error": "Scheduler not running"}
        except Exception as e:
            logger.error(f"Scheduler health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "status": "healthy",
                "rss_mb": round(memory_info.rss / 1024 / 1024, 2),
                "vms_mb": round(memory_info.vms / 1024 / 1024, 2),
                "memory_percent": round(process.memory_percent(), 2),
            }
        except ImportError:
            # psutil not available, skip memory check
            return {"status": "skipped", "error": "psutil not installed"}
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_uptime(self) -> str:
        """Get bot uptime"""
        uptime = datetime.now(timezone.utc) - self.startup_time
        hours, remainder = divmod(uptime.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)

        return f"{int(hours)}h {int(minutes)}m {int(seconds)}s"

    async def get_full_status(self) -> Dict[str, Any]:
        """Get complete health status"""
        uptime = await self.get_uptime()

        # Run all checks and handle exceptions individually
        try:
            db_check = await self.check_database()
        except Exception as e:
            db_check = {"status": "unhealthy", "error": str(e)}

        try:
            scheduler_check = await self.check_scheduler()
        except Exception as e:
            scheduler_check = {"status": "unhealthy", "error": str(e)}

        try:
            memory_check = await self.check_memory_usage()
        except Exception as e:
            memory_check = {"status": "unhealthy", "error": str(e)}

        # Determine overall status
        overall_status = "healthy"
        unhealthy_services = []

        for service_name, service_result in [
            ("database", db_check),
            ("scheduler", scheduler_check),
        ]:
            status = (
                service_result.get("status")
                if hasattr(service_result, "get")
                else "unhealthy"
            )
            error = (
                service_result.get("error")
                if hasattr(service_result, "get")
                else "Unknown error"
            )

            if status != "healthy" and status != "skipped":
                overall_status = "unhealthy"
                unhealthy_services.append(f"{service_name}: {error}")

        return {
            "status": overall_status,
            "uptime": uptime,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "database": db_check,
                "scheduler": scheduler_check,
                "memory": memory_check,
            },
            "unhealthy_services": unhealthy_services if unhealthy_services else None,
        }


class HealthCheckerManager:
    """Manager for health checker instance"""

    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance

    @classmethod
    def initialize(cls, session_factory=None):
        cls._instance = HealthChecker(session_factory)
        return cls._instance


# Global instance getter
def get_health_checker():
    return HealthCheckerManager.get_instance()


async def health_check_handler() -> Dict[str, Any]:
    """Main health check endpoint"""
    try:
        checker = get_health_checker()
        if checker is None:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": "Health checker not initialized",
            }
        return await checker.get_full_status()
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e),
        }
