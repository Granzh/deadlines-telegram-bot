from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from handlers.notifications import (
    notifications_command,
    toggle_notification,
)


class TestNotificationsHandlers:
    """Test cases for notifications handlers"""

    @pytest.mark.asyncio
    async def test_notifications_command(self):
        """Test notifications command with all settings enabled"""
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 12345

        mock_notification_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.notify_on_due = True
        mock_settings.notify_1_hour = True
        mock_settings.notify_3_hours = True
        mock_settings.notify_1_day = True
        mock_settings.notify_3_days = True
        mock_settings.notify_1_week = True
        mock_notification_service.get_or_create_settings.return_value = mock_settings

        await notifications_command(mock_message, mock_notification_service)

        mock_notification_service.get_or_create_settings.assert_called_once_with(12345)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert (
            call_args[0][0]
            == "⚙️ *Настройки уведомлений*\n\nВыбери, когда хочешь получать напоминания:\n\n✅ При наступлении срока\n✅ За 1 час\n✅ За 3 часа\n✅ За 1 день\n✅ За 3 дня\n✅ За неделю\n"
        )
        assert call_args[1]["reply_markup"] is not None
        assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_notifications_command_no_user(self):
        """Test notifications command with no user"""
        mock_message = Mock(spec=Message)
        mock_message.from_user = None
        mock_message.answer = AsyncMock()

        mock_notification_service = AsyncMock()

        await notifications_command(mock_message, mock_notification_service)

        mock_notification_service.get_or_create_settings.assert_not_called()
        mock_message.answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_notifications_command_mixed_settings(self):
        """Test notifications command with mixed notification settings"""
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 12345

        mock_notification_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.notify_on_due = True
        mock_settings.notify_1_hour = False
        mock_settings.notify_3_hours = True
        mock_settings.notify_1_day = False
        mock_settings.notify_3_days = True
        mock_settings.notify_1_week = False
        mock_notification_service.get_or_create_settings.return_value = mock_settings

        await notifications_command(mock_message, mock_notification_service)

        call_text = mock_message.answer.call_args[0][0]
        assert "✅ При наступлении срока" in call_text
        assert "❌ За 1 час" in call_text
        assert "✅ За 3 часа" in call_text
        assert "❌ За 1 день" in call_text
        assert "✅ За 3 дня" in call_text
        assert "❌ За неделю" in call_text

    @pytest.mark.asyncio
    async def test_toggle_notification_on_due(self):
        """Test toggling notification on due"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "notif_toggle:notify_on_due"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 12345
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.edit_text = AsyncMock()

        mock_notification_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.notify_on_due = True
        mock_settings.notify_1_hour = True
        mock_settings.notify_3_hours = True
        mock_settings.notify_1_day = True
        mock_settings.notify_3_days = True
        mock_settings.notify_1_week = True
        mock_notification_service.get_or_create_settings.return_value = mock_settings

        await toggle_notification(mock_callback, mock_notification_service)

        # Called twice: once to get current value, once to get updated value
        assert mock_notification_service.get_or_create_settings.call_count == 2
        mock_notification_service.update_settings.assert_called_once_with(
            12345, notify_on_due=False
        )
        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once_with("Настройка обновлена!")

    @pytest.mark.asyncio
    async def test_toggle_notification_1_hour(self):
        """Test toggling notification 1 hour"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "notif_toggle:notify_1_hour"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 12345
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.edit_text = AsyncMock()

        mock_notification_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.notify_on_due = True
        mock_settings.notify_1_hour = False
        mock_settings.notify_3_hours = True
        mock_settings.notify_1_day = True
        mock_settings.notify_3_days = True
        mock_settings.notify_1_week = True
        mock_notification_service.get_or_create_settings.return_value = mock_settings

        await toggle_notification(mock_callback, mock_notification_service)

        # Called twice: once to get current value, once to get updated value
        assert mock_notification_service.get_or_create_settings.call_count == 2
        mock_notification_service.update_settings.assert_called_once_with(
            12345, notify_1_hour=True
        )
        mock_callback.message.edit_text.assert_called_once()
        mock_callback.answer.assert_called_once_with("Настройка обновлена!")

    @pytest.mark.asyncio
    async def test_toggle_notification_inaccessible_message(self):
        """Test toggling notification with inaccessible message"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "notif_toggle:notify_3_hours"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 12345
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock(spec=InaccessibleMessage)

        mock_notification_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.notify_on_due = True
        mock_settings.notify_1_hour = True
        mock_settings.notify_3_hours = True
        mock_settings.notify_1_day = True
        mock_settings.notify_3_days = True
        mock_settings.notify_1_week = True
        mock_notification_service.get_or_create_settings.return_value = mock_settings

        await toggle_notification(mock_callback, mock_notification_service)

        mock_notification_service.update_settings.assert_called_once()
        mock_callback.answer.assert_called_once_with("Настройка обновлена!")

    @pytest.mark.asyncio
    async def test_toggle_notification_message_edit_fails(self):
        """Test toggling notification when message edit fails"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "notif_toggle:notify_1_day"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 12345
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.edit_text = AsyncMock(
            side_effect=Exception("Edit failed")
        )

        mock_notification_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.notify_on_due = True
        mock_settings.notify_1_hour = True
        mock_settings.notify_3_hours = True
        mock_settings.notify_1_day = True
        mock_settings.notify_3_days = True
        mock_settings.notify_1_week = True
        mock_notification_service.get_or_create_settings.return_value = mock_settings

        await toggle_notification(mock_callback, mock_notification_service)

        mock_notification_service.update_settings.assert_called_once()
        mock_callback.answer.assert_called_once_with("Настройка обновлена!")

    @pytest.mark.asyncio
    async def test_toggle_notification_no_message(self):
        """Test toggling notification with no message"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "notif_toggle:notify_3_days"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 12345
        mock_callback.answer = AsyncMock()
        mock_callback.message = None

        mock_notification_service = AsyncMock()
        mock_settings = Mock()
        mock_settings.notify_on_due = True
        mock_settings.notify_1_hour = True
        mock_settings.notify_3_hours = True
        mock_settings.notify_1_day = True
        mock_settings.notify_3_days = True
        mock_settings.notify_1_week = True
        mock_notification_service.get_or_create_settings.return_value = mock_settings

        await toggle_notification(mock_callback, mock_notification_service)

        mock_notification_service.update_settings.assert_called_once()
        mock_callback.answer.assert_called_once_with("Настройка обновлена!")

    @pytest.mark.asyncio
    async def test_toggle_notification_all_fields(self):
        """Test toggling all notification fields"""
        fields = [
            "notify_on_due",
            "notify_1_hour",
            "notify_3_hours",
            "notify_1_day",
            "notify_3_days",
            "notify_1_week",
        ]

        for field in fields:
            mock_callback = Mock(spec=CallbackQuery)
            mock_callback.data = f"notif_toggle:{field}"
            mock_callback.from_user = Mock()
            mock_callback.from_user.id = 12345
            mock_callback.answer = AsyncMock()
            mock_callback.message = Mock()
            mock_callback.message.edit_text = AsyncMock()

            mock_notification_service = AsyncMock()
            mock_settings = Mock()
            # Set all to True initially
            for f in fields:
                setattr(mock_settings, f, True)
            mock_notification_service.get_or_create_settings.return_value = (
                mock_settings
            )

            await toggle_notification(mock_callback, mock_notification_service)

            assert mock_notification_service.get_or_create_settings.call_count == 2
            mock_notification_service.update_settings.assert_called_once_with(
                12345, **{field: False}
            )
            mock_callback.message.edit_text.assert_called_once()
            mock_callback.answer.assert_called_once_with("Настройка обновлена!")
