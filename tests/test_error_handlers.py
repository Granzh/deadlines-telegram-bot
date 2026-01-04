from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TelegramUser

from exceptions import (
    CallbackDataError,
    DatabaseError,
    DeadlineNotFoundError,
    ValidationError,
)
from utils.error_handler import ErrorHandler, handle_callback_errors, handle_errors


class TestErrorHandlers:
    """Test cases for error handling decorators"""

    @pytest.mark.asyncio
    async def test_handle_errors_success(self):
        """Test successful function execution with error handler"""

        @handle_errors("Test error message")
        async def test_func(message):
            return "success"

        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        result = await test_func(mock_message)

        assert result == "success"
        mock_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_errors_validation_error(self):
        """Test handling ValidationError"""

        @handle_errors("Default error")
        async def test_func(message):
            raise ValidationError("Invalid input")

        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        result = await test_func(mock_message)

        assert result is None
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Default error" in call_args
        assert "Invalid input" in call_args

    @pytest.mark.asyncio
    async def test_handle_errors_database_error(self):
        """Test handling DatabaseError"""

        @handle_errors("Default error")
        async def test_func(message):
            raise DatabaseError("Database connection failed")

        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        result = await test_func(mock_message)

        assert result is None
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Ошибка базы данных" in call_args

    @pytest.mark.asyncio
    async def test_handle_errors_general_error(self):
        """Test handling general Exception"""

        @handle_errors("Default error")
        async def test_func(message):
            raise Exception("Unexpected error")

        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        result = await test_func(mock_message)

        assert result is None
        mock_message.answer.assert_called_once_with("Default error")

    @pytest.mark.asyncio
    async def test_handle_errors_custom_message(self):
        """Test custom error message"""

        @handle_errors("Custom error message")
        async def test_func(message):
            raise Exception("Test error")

        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        await test_func(mock_message)

        mock_message.answer.assert_called_once_with("Custom error message")

    @pytest.mark.asyncio
    async def test_handle_callback_errors_success(self):
        """Test successful callback execution with error handler"""

        @handle_callback_errors("Test error")
        async def test_callback(callback):
            return "success"

        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock()

        result = await test_callback(mock_callback)

        assert result == "success"
        mock_callback.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_callback_errors_validation_error_alert(self):
        """Test handling ValidationError with alert"""

        @handle_callback_errors("Default error")
        async def test_callback(callback):
            raise ValidationError("Invalid callback data")

        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock()

        result = await test_callback(mock_callback)

        assert result is None
        mock_callback.answer.assert_called_once()
        call_args, call_kwargs = mock_callback.answer.call_args
        assert "Default error" in call_args[0]
        assert "Invalid callback data" in call_args[0]
        assert call_kwargs.get("show_alert") is True

    @pytest.mark.asyncio
    async def test_handle_callback_errors_database_error(self):
        """Test handling DatabaseError in callback"""

        @handle_callback_errors("Default error")
        async def test_callback(callback):
            raise DatabaseError("Database error")

        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock()

        result = await test_callback(mock_callback)

        assert result is None
        mock_callback.answer.assert_called_once()
        call_args, call_kwargs = mock_callback.answer.call_args
        assert "Ошибка базы данных" in call_args[0]
        assert call_kwargs.get("show_alert") is True

    @pytest.mark.asyncio
    async def test_handle_callback_errors_general_error_no_alert(self):
        """Test handling general Exception without alert"""

        @handle_callback_errors("Default error")
        async def test_callback(callback):
            raise Exception("Unexpected error")

        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock()

        result = await test_callback(mock_callback)

        assert result is None
        mock_callback.answer.assert_called_once_with("Default error", show_alert=False)

    @pytest.mark.asyncio
    async def test_handle_errors_deadline_bot_error(self):
        """Test handling DeadlineBotError"""
        from exceptions import DeadlineBotError

        with patch("utils.error_handler._send_error_message") as send_error_mock:

            @handle_errors("Custom error")
            async def test_handler(*args, **kwargs):
                raise DeadlineBotError("Custom error")

            mock_callback = Mock(spec=CallbackQuery)
            mock_callback.answer = AsyncMock()

            result = await test_handler(mock_callback)

            assert result is None
            send_error_mock.assert_awaited_once()
            mock_callback.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_error_message_message_type(self):
        """Test sending error message to Message"""
        from utils.error_handler import _send_error_message

        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        await _send_error_message((mock_message,), "Test error", "Details")

        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Test error" in call_args
        assert "Details" in call_args

    @pytest.mark.asyncio
    async def test_send_error_message_callback_type(self):
        """Test sending error message to CallbackQuery"""
        from utils.error_handler import _send_error_message

        mock_callback = Mock(spec=CallbackQuery)
        mock_message = Mock(spec=Message)
        mock_callback.message = mock_message
        mock_message.answer = AsyncMock()

        await _send_error_message((mock_callback,), "Test error")

        mock_message.answer.assert_called_once_with("Test error")

    @pytest.mark.asyncio
    async def test_send_error_message_no_message_or_callback(self):
        """Test error when no message or callback found"""
        from utils.error_handler import _send_error_message

        with patch("utils.error_handler.logger") as mock_logger:
            mock_logger.error = Mock()

            await _send_error_message(("not_a_message",), "Test error")

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_answer_callback_success(self):
        """Test answering callback successfully"""
        from utils.error_handler import _answer_callback

        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock()

        await _answer_callback(
            (mock_callback,), "Test error", "Details", show_alert=True
        )

        mock_callback.answer.assert_called_once()
        call_args, call_kwargs = mock_callback.answer.call_args
        assert "Test error" in call_args[0]
        assert "Details" in call_args[0]
        assert call_kwargs.get("show_alert") is True

    @pytest.mark.asyncio
    async def test_answer_callback_no_callback(self):
        """Test error when no callback found"""
        from utils.error_handler import _answer_callback

        with patch("utils.error_handler.logger") as mock_logger:
            mock_logger.error = Mock()

            await _answer_callback(("not_a_callback",), "Test error")

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_answer_callback_answer_failure(self):
        """Test handling callback answer failure"""
        from utils.error_handler import _answer_callback

        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock(side_effect=Exception("Answer failed"))

        with patch("utils.error_handler.logger") as mock_logger:
            mock_logger.error = Mock()

            await _answer_callback((mock_callback,), "Test error")

            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handler_unknown_message(self):
        """Test ErrorHandler.handle_unknown_message"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345

        mock_message = Mock(spec=Message)
        mock_message.from_user = mock_user
        mock_message.text = "/unknown"
        mock_message.answer = AsyncMock()

        await ErrorHandler.handle_unknown_message(mock_message)

        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Неизвестная команда" in call_args

    @pytest.mark.asyncio
    async def test_error_handler_unknown_message_no_user(self):
        """Test ErrorHandler.handle_unknown_message with no user"""
        mock_message = Mock(spec=Message)
        mock_message.from_user = None
        mock_message.answer = AsyncMock()

        await ErrorHandler.handle_unknown_message(mock_message)

        # Should still answer even without user
        mock_message.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handler_rate_limit(self):
        """Test ErrorHandler.handle_rate_limit"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345

        mock_message = Mock(spec=Message)
        mock_message.from_user = mock_user
        mock_message.answer = AsyncMock()

        await ErrorHandler.handle_rate_limit(mock_message)

        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Слишком много запросов" in call_args

    @pytest.mark.asyncio
    async def test_error_handler_rate_limit_no_user(self):
        """Test ErrorHandler.handle_rate_limit with no user"""
        mock_message = Mock(spec=Message)
        mock_message.from_user = None
        mock_message.answer = AsyncMock()

        await ErrorHandler.handle_rate_limit(mock_message)

        # Should still answer even without user
        mock_message.answer.assert_called_once()

    def test_handle_errors_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata"""

        @handle_errors("Test error")
        async def test_function(message: Message) -> str:
            """Test function docstring"""
            return "test"

        assert test_function.__name__ == "test_function"
        assert test_function.__doc__ == "Test function docstring"
        assert hasattr(test_function, "__wrapped__")

    @pytest.mark.asyncio
    async def test_handle_callback_errors_decorator_preserves_metadata(self):
        """Test that callback decorator preserves function metadata"""

        @handle_callback_errors("Test error")
        async def test_callback(callback: CallbackQuery) -> str:
            """Test callback docstring"""
            return "test"

        assert test_callback.__name__ == "test_callback"
        assert test_callback.__doc__ == "Test callback docstring"
        assert hasattr(test_callback, "__wrapped__")

    @pytest.mark.asyncio
    async def test_send_error_message_answer_failure(self):
        """Test handling failure when sending error message (covers lines 76-77)"""
        from utils.error_handler import _send_error_message

        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock(side_effect=Exception("Failed to send"))

        with patch("utils.error_handler.logger") as mock_logger:
            mock_logger.error = Mock()

            await _send_error_message((mock_message,), "Test error")

            # Should log the error but not crash
            mock_logger.error.assert_called_once_with(
                "Failed to send error message: Failed to send"
            )

    @pytest.mark.asyncio
    async def test_handle_callback_errors_deadline_bot_error(self):
        """Test handling DeadlineBotError in callback (covers lines 104-106)"""
        from exceptions import DeadlineBotError

        @handle_callback_errors("Custom error")
        async def test_callback(callback):
            raise DeadlineBotError("Deadline specific error")

        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.answer = AsyncMock()

        result = await test_callback(mock_callback)

        assert result is None
        mock_callback.answer.assert_called_once_with("Custom error", show_alert=False)
