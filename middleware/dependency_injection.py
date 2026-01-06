from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable

from services.deadline_service import DeadlineService
from services.notification_service import NotificationService


class DependencyInjectionMiddleware(BaseMiddleware):
    """Middleware for dependency injection of services into handlers"""

    def __init__(
        self,
        deadline_service: DeadlineService,
        notification_service: NotificationService,
    ):
        self.deadline_service = deadline_service
        self.notification_service = notification_service

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Inject services into data
        data["deadline_service"] = self.deadline_service
        data["notification_service"] = self.notification_service

        return await handler(event, data)
