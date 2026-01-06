import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from utils.health import (
    HealthChecker,
    HealthCheckerManager,
    health_check_handler,
)


class TestHealthChecker:
    """Test suite for HealthChecker"""

    @pytest.fixture
    def mock_session_factory(self):
        """Mock session factory"""
        return MagicMock()

    @pytest.fixture
    def health_checker(self, mock_session_factory):
        """Create health checker instance"""
        return HealthChecker(mock_session_factory)

    @pytest.mark.asyncio
    async def test_init(self, mock_session_factory):
        """Test health checker initialization"""
        checker = HealthChecker(mock_session_factory)
        assert checker.session_factory == mock_session_factory
        assert checker.startup_time is not None

    @pytest.mark.asyncio
    async def test_check_database_success(self, health_checker):
        """Test successful database check"""
        with patch.object(health_checker, "session_factory") as mock_factory:
            mock_session = MagicMock()
            mock_factory.return_value = mock_session
            mock_session.execute = MagicMock()
            mock_session.execute.return_value = MagicMock()

            result = await health_checker.check_database()

            assert result["status"] == "healthy"
            assert "response" in result

    @pytest.mark.asyncio
    async def test_check_database_failure(self, health_checker):
        """Test database check failure"""
        with patch.object(health_checker, "session_factory") as mock_factory:
            mock_factory.side_effect = Exception("Database error")

            result = await health_checker.check_database()

            assert result["status"] == "unhealthy"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_check_scheduler_running(self, health_checker):
        """Test scheduler check when running"""
        mock_scheduler = MagicMock()
        mock_scheduler.running = True
        mock_scheduler.get_jobs.return_value = [MagicMock(), MagicMock()]

        with patch.object(health_checker, "check_scheduler") as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "scheduler_running": True,
                "jobs_count": 2,
            }
            result = await health_checker.check_scheduler()

        assert result["status"] == "healthy"
        assert result["scheduler_running"] is True
        assert result["jobs_count"] == 2

    @pytest.mark.asyncio
    async def test_check_scheduler_not_running(self, health_checker):
        """Test scheduler check when not running"""
        with patch.object(health_checker, "check_scheduler") as mock_check:
            mock_check.return_value = {
                "status": "unhealthy",
                "error": "Scheduler not running",
            }
            result = await health_checker.check_scheduler()

        assert result["status"] == "unhealthy"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_check_memory_usage(self, health_checker):
        """Test memory usage check"""
        with patch.object(health_checker, "check_memory_usage") as mock_check:
            mock_check.return_value = {
                "status": "healthy",
                "rss_mb": 100.0,
                "vms_mb": 200.0,
                "memory_percent": 50.5,
            }
            result = await health_checker.check_memory_usage()

            assert result["status"] == "healthy"
            assert result["rss_mb"] == 100.0
            assert result["vms_mb"] == 200.0
            assert result["memory_percent"] == 50.5

    @pytest.mark.asyncio
    async def test_check_memory_usage_no_psutil(self, health_checker):
        """Test memory usage check when psutil not available"""
        with patch.object(health_checker, "check_memory_usage") as mock_check:
            mock_check.return_value = {
                "status": "skipped",
                "error": "psutil not installed",
            }
            result = await health_checker.check_memory_usage()

            assert result["status"] == "skipped"
            assert "psutil not installed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_uptime(self, health_checker):
        """Test uptime calculation"""
        with patch("datetime.datetime") as mock_datetime:
            # Mock current time to be 5 hours after startup
            health_checker.startup_time = datetime.now(timezone.utc) - timedelta(
                hours=1
            )

            result = await health_checker.get_uptime()

            assert result.startswith("1h")

    @pytest.mark.asyncio
    async def test_get_full_status_healthy(self, health_checker):
        """Test full status when all services are healthy"""
        with (
            patch.object(health_checker, "check_database") as mock_db,
            patch.object(health_checker, "check_scheduler") as mock_scheduler,
            patch.object(health_checker, "check_memory_usage") as mock_memory,
            patch.object(health_checker, "get_uptime") as mock_uptime,
        ):
            mock_db.return_value = {"status": "healthy"}
            mock_scheduler.return_value = {"status": "healthy"}
            mock_memory.return_value = {"status": "healthy"}
            mock_uptime.return_value = "2h 30m 15s"

            result = await health_checker.get_full_status()

            assert result["status"] == "healthy"
            assert result["uptime"] == "2h 30m 15s"
            assert "timestamp" in result
            assert "services" in result
            assert result["services"]["database"]["status"] == "healthy"
            assert result["services"]["scheduler"]["status"] == "healthy"
            assert result["services"]["memory"]["status"] == "healthy"
            assert result["unhealthy_services"] is None

    @pytest.mark.asyncio
    async def test_get_full_status_unhealthy(self, health_checker):
        """Test full status when some services are unhealthy"""
        with (
            patch.object(health_checker, "check_database") as mock_db,
            patch.object(health_checker, "check_scheduler") as mock_scheduler,
            patch.object(health_checker, "check_memory_usage") as mock_memory,
            patch.object(health_checker, "get_uptime") as mock_uptime,
        ):
            mock_db.return_value = {"status": "healthy"}
            mock_scheduler.return_value = {
                "status": "unhealthy",
                "error": "Not running",
            }
            mock_memory.return_value = {"status": "healthy"}
            mock_uptime.return_value = "1h 15m 30s"

            result = await health_checker.get_full_status()

            assert result["status"] == "unhealthy"
            assert result["uptime"] == "1h 15m 30s"
            assert result["unhealthy_services"] is not None
            assert "scheduler: Not running" in result["unhealthy_services"]


class TestHealthCheckerManager:
    """Test suite for HealthCheckerManager"""

    def test_get_instance_none(self):
        """Test get_instance when not initialized"""
        manager = HealthCheckerManager.get_instance()
        assert manager is None

    def test_initialize(self):
        """Test manager initialization"""
        mock_session_factory = MagicMock()
        manager = HealthCheckerManager.initialize(mock_session_factory)

        assert isinstance(manager, HealthChecker)
        assert manager.session_factory == mock_session_factory

        # Test get_instance after initialization
        retrieved = HealthCheckerManager.get_instance()
        assert retrieved is manager

    def test_initialize_override(self):
        """Test that initialize overrides existing instance"""
        mock_session_factory1 = MagicMock()
        manager1 = HealthCheckerManager.initialize(mock_session_factory1)

        mock_session_factory2 = MagicMock()
        manager2 = HealthCheckerManager.initialize(mock_session_factory2)

        assert manager2.session_factory == mock_session_factory2
        assert manager2 is not manager1


class TestHealthCheckHandler:
    """Test suite for health check handler"""

    @pytest.mark.asyncio
    async def test_health_check_handler_success(self):
        """Test health check handler success"""
        with patch("utils.health.get_health_checker") as mock_get_checker:
            mock_checker = MagicMock()
            mock_checker.get_full_status = AsyncMock(
                return_value={
                    "status": "healthy",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
            mock_get_checker.return_value = mock_checker

            result = await health_check_handler()

            assert result["status"] == "healthy"
            assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_health_check_handler_no_checker(self):
        """Test health check handler when checker not initialized"""
        with patch("utils.health.get_health_checker") as mock_get_checker:
            mock_get_checker.return_value = None

            result = await health_check_handler()

            assert result["status"] == "unhealthy"
            assert "error" in result

    @pytest.mark.asyncio
    async def test_health_check_handler_exception(self):
        """Test health check handler when exception occurs"""
        with patch("utils.health.get_health_checker") as mock_get_checker:
            mock_checker = MagicMock()
            mock_checker.get_full_status = AsyncMock(
                return_value={"status": "unhealthy", "error": "Test error"}
            )
            mock_get_checker.return_value = mock_checker

            result = await health_check_handler()

            assert result["status"] == "unhealthy"
            assert "error" in result
            assert "Test error" in result["error"]
