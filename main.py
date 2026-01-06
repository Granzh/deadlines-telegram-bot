import asyncio
import signal
import sys

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

from config import settings
from db.session import create_engine_and_session, init_db
from handlers.base_handlers import router
from handlers.delete_deadline import delete_deadline_router
from handlers.edit_deadline import edit_deadline_router
from handlers.help import help_router
from handlers.notifications import notifications_router
from handlers.start_router import start_router
from middleware.dependency_injection import DependencyInjectionMiddleware
from middleware.rate_limit import RateLimitMiddleware
from scheduler import setup_scheduler
from services.deadline_service import DeadlineService
from services.notification_service import NotificationService
from utils.health import HealthCheckerManager

assert settings.bot_token is not None


async def main():
    bot = Bot(settings.bot_token)
    dp = Dispatcher()

    # Create engine and session
    engine, session_factory = create_engine_and_session(settings.database_url)
    await init_db(engine)

    # Initialize health checker
    HealthCheckerManager.initialize(session_factory)

    deadline_service = DeadlineService(session_factory)
    notification_service = NotificationService(session_factory)

    # Add rate limiting middleware
    dp.message.middleware(RateLimitMiddleware(time_limit=10, max_calls=5))
    dp.callback_query.middleware(RateLimitMiddleware(time_limit=10, max_calls=5))

    # Add dependency injection middleware
    dp.message.middleware(
        DependencyInjectionMiddleware(deadline_service, notification_service)
    )
    dp.callback_query.middleware(
        DependencyInjectionMiddleware(deadline_service, notification_service)
    )

    commands = [
        BotCommand(command="start", description="Запуск бота"),
        BotCommand(command="help", description="Список команд"),
        BotCommand(command="add", description="Добавить дедлайн"),
        BotCommand(command="list", description="Список дедлайнов"),
        BotCommand(command="edit", description="Редактировать дедлайн"),
        BotCommand(command="delete", description="Удалить дедлайн"),
        BotCommand(command="notifications", description="Настройки уведомлений"),
        BotCommand(command="change_timezone", description="Настройки часового пояса"),
    ]

    dp.include_router(router)
    dp.include_router(start_router)
    dp.include_router(help_router)
    dp.include_router(edit_deadline_router)
    dp.include_router(delete_deadline_router)
    dp.include_router(notifications_router)

    await bot.set_my_commands(commands)

    setup_scheduler(bot, deadline_service, notification_service)

    # Graceful shutdown handlers
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, shutting down gracefully...")
        asyncio.create_task(shutdown(bot))

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start health server in background
    import threading

    def run_health_server():
        import subprocess

        try:
            # Run health server in subprocess
            subprocess.run(["uv", "run", "python", "health_server.py"], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Health server failed: {e}")
        except Exception as e:
            print(f"Failed to start health server: {e}")

    # Start health server in background thread
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()

    # Give health server time to start
    await asyncio.sleep(2)

    print("Bot and health server started")
    await dp.start_polling(bot)


async def shutdown(bot: Bot):
    """Graceful shutdown procedure"""
    print("Starting graceful shutdown...")

    try:
        # Stop receiving updates
        await bot.session.close()

        # Stop scheduler
        from scheduler import get_scheduler_instance

        scheduler = get_scheduler_instance()
        if scheduler and scheduler.running:
            scheduler.shutdown()
            print("Scheduler stopped")

        print("Graceful shutdown completed")

    except Exception as e:
        print(f"Error during shutdown: {e}")
    finally:
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
