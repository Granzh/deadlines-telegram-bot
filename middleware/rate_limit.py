"""
Rate limiting middleware for Telegram bot
"""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from utils.logging_config import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseMiddleware):
    """Rate limiting middleware to prevent spam"""

    def __init__(self, time_limit: int = 10, max_calls: int = 5):
        """
        Initialize rate limiter

        Args:
            time_limit: Time window in seconds
            max_calls: Maximum number of calls allowed in time window
        """
        self.limit = timedelta(seconds=time_limit)
        self.max_calls = max_calls
        self.calls: Dict[int, list] = defaultdict(list)

    async def __call__(self, handler, event, data):
        """Check rate limit and process event"""
        user_id = self._get_user_id(event)

        if not user_id:
            return await handler(event, data)

        # Clean old calls
        now = datetime.now()
        self.calls[user_id] = [
            call_time
            for call_time in self.calls[user_id]
            if now - call_time < self.limit
        ]

        # Check if user exceeded limit
        if len(self.calls[user_id]) >= self.max_calls:
            logger.warning(f"Rate limit exceeded for user {user_id}")
            await self._handle_rate_limit_exceeded(event)
            return

        # Record this call
        self.calls[user_id].append(now)

        return await handler(event, data)

    def _get_user_id(self, event):
        """Extract user ID from event"""
        if isinstance(event, Message):
            return event.from_user.id
        elif isinstance(event, CallbackQuery):
            return event.from_user.id
        return None

    async def _handle_rate_limit_exceeded(self, event):
        """Handle rate limit exceeded event"""
        message = (
            "Too many requests! Please wait a moment before trying again.\n"
            f"You can send up to {self.max_calls} messages per {self.limit.total_seconds()} seconds."
        )

        if isinstance(event, Message):
            await event.answer(message)
        elif isinstance(event, CallbackQuery):
            await event.message.answer(message)
            await event.answer()  # Stop callback loading
