from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import CallbackQuery
from aiogram.types import User as TelegramUser

from exceptions import CallbackDataError
from handlers.delete_deadline import delete_deadline


class TestDeleteDeadline:
    """Test cases for delete deadline handler"""

    @pytest.mark.asyncio
    async def test_delete_deadline_success(self):
        """Test successful deadline deletion"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 456
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "delete:123"
        mock_callback.from_user = mock_user
        mock_callback.answer = AsyncMock()

        mock_message = Mock()
        mock_message.edit_text = AsyncMock()
        mock_callback.message = mock_message

        mock_deadline_service = AsyncMock()
        mock_deadline_service.delete = AsyncMock()

        await delete_deadline(mock_callback, mock_deadline_service)

        mock_deadline_service.delete.assert_called_once_with(123, 456)
        mock_message.edit_text.assert_called_once_with(
            "✅ Дедлайн удален", parse_mode="Markdown"
        )
        mock_callback.answer.assert_called_once_with(
            "Дедлайн удален", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_delete_deadline_no_callback_data(self):
        """Test delete deadline with no callback data"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = None
        mock_callback.answer = AsyncMock()
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 123

        mock_deadline_service = AsyncMock()

        result = await delete_deadline(mock_callback, mock_deadline_service)

        assert result is None

        mock_deadline_service.delete.assert_not_called()

        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_deadline_invalid_callback_data(self):
        """Test delete deadline with invalid callback data format"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "delete_invalid"
        mock_callback.answer = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline_service.delete = AsyncMock()

        result = await delete_deadline(mock_callback, mock_deadline_service)

        assert result is None

        mock_deadline_service.delete.assert_not_called()

        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_deadline_invalid_deadline_id(self):
        """Test delete deadline with invalid deadline ID"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "delete:invalid_id"
        mock_callback.answer = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline_service.delete = AsyncMock()

        result = await delete_deadline(mock_callback, mock_deadline_service)

        assert result is None

        mock_deadline_service.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_deadline_no_message(self):
        """Test delete deadline when callback has no message"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 456
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "delete:123"
        mock_callback.from_user = mock_user
        mock_callback.answer = AsyncMock()
        mock_callback.message = None

        mock_deadline_service = AsyncMock()
        mock_deadline_service.delete = AsyncMock()

        await delete_deadline(mock_callback, mock_deadline_service)

        mock_deadline_service.delete.assert_called_once_with(123, 456)
        mock_callback.answer.assert_called_once_with(
            "Дедлайн удален", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_delete_deadline_message_without_edit_text(self):
        """Test delete deadline when message doesn't have edit_text method"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 456
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "delete:123"
        mock_callback.from_user = mock_user
        mock_callback.answer = AsyncMock()

        mock_message = Mock()
        del mock_message.edit_text  # Remove edit_text attribute
        mock_callback.message = mock_message

        mock_deadline_service = AsyncMock()
        mock_deadline_service.delete = AsyncMock()

        await delete_deadline(mock_callback, mock_deadline_service)

        mock_deadline_service.delete.assert_called_once_with(123, 456)
        mock_callback.answer.assert_called_once_with(
            "Дедлайн удален", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_delete_deadline_message_edit_text_fails(self):
        """Test delete deadline when message edit_text fails"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 456
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "delete:123"
        mock_callback.from_user = mock_user
        mock_callback.answer = AsyncMock()

        mock_message = Mock()
        mock_message.edit_text = AsyncMock(side_effect=Exception("Message too old"))
        mock_callback.message = mock_message

        mock_deadline_service = AsyncMock()
        mock_deadline_service.delete = AsyncMock()

        await delete_deadline(mock_callback, mock_deadline_service)

        mock_deadline_service.delete.assert_called_once_with(123, 456)
        mock_callback.answer.assert_called_once_with(
            "Дедлайн удален", parse_mode="Markdown"
        )
