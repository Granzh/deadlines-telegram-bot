import logging
import re
from functools import wraps
from typing import Callable, Any, Awaitable

from aiogram import types
from aiogram.types import Message, CallbackQuery

from exceptions import DeadlineBotError, ValidationError, DatabaseError


logger = logging.getLogger(__name__)


def _sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages"""
    if not message:
        return "Unknown error"

    # Remove potential sensitive patterns
    message = re.sub(r"\b\d{10,}\b", "[ID]", message)  # Long numbers
    message = re.sub(r'token[_\s]*=[\s\'"]+[a-zA-Z0-9_-]+', "token=[REDACTED]", message)
    message = re.sub(
        r'password[_\s]*=[\s\'"]+[^\s\'"]+', "password=[REDACTED]", message
    )
    message = re.sub(r'secret[_\s]*=[\s\'"]+[^\s\'"]+', "secret=[REDACTED]", message)
    message = re.sub(
        r'api[_\s]*key[_\s]*=[\s\'"]+[^\s\'"]+', "api_key=[REDACTED]", message
    )

    # Remove file paths
    message = re.sub(r"/[^/\s]+/[^/\s]+", "[PATH]", message)
    message = re.sub(r"[A-Za-z]:\\[^\\\s]+\\[^\\\s]+", "[PATH]", message)

    # Limit length
    if len(message) > 200:
        message = message[:200] + "..."

    return message


def handle_errors(message: str = "Произошла ошибка. Попробуйте позже.") -> Callable:
    """Decorator for handling errors in bot handlers"""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)

            except ValidationError as e:
                sanitized_error = _sanitize_error_message(str(e))
                logger.warning(
                    f"Validation error in {func.__name__}: {sanitized_error}"
                )
                await _send_error_message(args, message, "Invalid input provided")
                return None

            except DatabaseError as e:
                logger.error(f"Database error in {func.__name__}: {e}")
                await _send_error_message(args, "Ошибка базы данных. Попробуйте позже.")
                return None

            except DeadlineBotError as e:
                logger.error(f"Application error in {func.__name__}: {e}")
                await _send_error_message(args, message)
                return None

            except Exception as e:
                sanitized_error = _sanitize_error_message(str(e))
                logger.critical(
                    f"Unexpected error in {func.__name__}: {sanitized_error}",
                    exc_info=True,
                )
                await _send_error_message(args, message)
                return None

        return wrapper

    return decorator


async def _send_error_message(
    args: tuple, default_message: str, details: str | None = None
) -> None:
    """Send error message to user"""

    # Find the message or callback query in args
    message_or_callback = None
    for arg in args:
        if isinstance(arg, (Message, CallbackQuery)):
            message_or_callback = arg
            break

    if not message_or_callback:
        logger.error("Cannot find message or callback to send error")
        return

    error_text = default_message
    if details:
        error_text += f"\n\n{details}"

    try:
        if isinstance(message_or_callback, CallbackQuery):
            if message_or_callback.message:
                await message_or_callback.message.answer(error_text)
        else:
            await message_or_callback.answer(error_text)
    except Exception as e:
        logger.error(f"Failed to send error message: {e}")


def handle_callback_errors(
    message: str = "Произошла ошибка. Попробуйте позже.",
) -> Callable:
    """Decorator for handling errors in callback handlers"""

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)

            except ValidationError as e:
                sanitized_error = _sanitize_error_message(str(e))
                logger.warning(
                    f"Validation error in callback {func.__name__}: {sanitized_error}"
                )
                await _answer_callback(
                    args, message, "Invalid input provided", show_alert=True
                )
                return None

            except DatabaseError as e:
                logger.error(f"Database error in callback {func.__name__}: {e}")
                await _answer_callback(
                    args, "Ошибка базы данных. Попробуйте позже.", show_alert=True
                )
                return None

            except DeadlineBotError as e:
                logger.error(f"Application error in callback {func.__name__}: {e}")
                await _answer_callback(args, message, show_alert=False)
                return None

            except Exception as e:
                logger.critical(
                    f"Unexpected error in callback {func.__name__}: {e}", exc_info=True
                )
                await _answer_callback(args, message, show_alert=False)
                return None

        return wrapper

    return decorator


async def _answer_callback(
    args: tuple, message: str, details: str | None = None, show_alert: bool = False
) -> None:
    """Answer callback query with error message"""

    # Find the callback query in args
    callback = None
    for arg in args:
        if isinstance(arg, CallbackQuery):
            callback = arg
            break

    if not callback:
        logger.error("Cannot find callback to answer with error")
        return

    error_text = message
    if details:
        error_text += f"\n\n{details}"

    try:
        await callback.answer(error_text, show_alert=show_alert)
    except Exception as e:
        logger.error(f"Failed to answer callback with error: {e}")


class ErrorHandler:
    """Centralized error handler for the bot"""

    @staticmethod
    async def handle_unknown_message(message: types.Message) -> None:
        """Handle unknown commands or messages"""
        if message.from_user:
            logger.warning(
                f"Unknown message from user {message.from_user.id}: {message.text}"
            )
        await message.answer(
            "Неизвестная команда. Используйте /help для списка доступных команд."
        )

    @staticmethod
    async def handle_rate_limit(message: types.Message) -> None:
        """Handle rate limiting"""
        if message.from_user:
            logger.warning(f"Rate limit exceeded for user {message.from_user.id}")
        await message.answer(
            "Слишком много запросов. Подождите немного перед следующей командой."
        )
