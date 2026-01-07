from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.types import User as TelegramUser

from handlers.base_handlers import (
    add_datetime,
    add_start,
    add_title,
    change_timezone_command,
    delete_deadline_command,
    list_deadlines,
)
from handlers.fsm_add_deadline import AddDeadlineFSM


class TestBaseHandlers:
    """Test cases for base handlers"""

    @pytest.mark.asyncio
    async def test_add_start_command(self):
        """Test add command starts FSM"""
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_state = Mock(spec=FSMContext)
        mock_state.set_state = AsyncMock()

        await add_start(mock_message, mock_state)

        mock_message.answer.assert_called_once_with("Enter the title of the deadline:")
        mock_state.set_state.assert_called_once_with(AddDeadlineFSM.title)

    @pytest.mark.asyncio
    async def test_list_deadlines_with_deadlines(self):
        """Test list command with existing deadlines"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_deadline_service = AsyncMock()
        mock_deadline_service.get_timezone_for_user.return_value = "UTC"

        future_date = datetime.now(timezone.utc) + timedelta(days=7)
        mock_deadline = Mock()
        mock_deadline.title = "Test Deadline"
        mock_deadline.deadline_at = future_date
        mock_deadline_service.list_for_user.return_value = [mock_deadline]

        await list_deadlines(mock_message, mock_deadline_service)

        mock_deadline_service.get_timezone_for_user.assert_called_once_with(12345)
        mock_deadline_service.list_for_user.assert_called_once_with(12345)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args[0][0]
        assert "Твои дедлайны:" in call_args
        assert "Test Deadline" in call_args

    @pytest.mark.asyncio
    async def test_list_deadlines_no_deadlines(self):
        """Test list command with no deadlines"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_deadline_service = AsyncMock()
        mock_deadline_service.get_timezone_for_user.return_value = "UTC"
        mock_deadline_service.list_for_user.return_value = []

        await list_deadlines(mock_message, mock_deadline_service)

        mock_deadline_service.get_timezone_for_user.assert_called_once_with(12345)
        mock_deadline_service.list_for_user.assert_called_once_with(12345)
        mock_message.answer.assert_called_once_with(
            "Нет дедлайнов!", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_change_timezone_success(self):
        """Test successful timezone change"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.text = "/change_timezone Europe/Moscow"
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_deadline_service = AsyncMock()
        mock_deadline_service.edit_timezone.return_value = True

        await change_timezone_command(mock_message, mock_deadline_service)

        mock_deadline_service.edit_timezone.assert_called_once_with(
            12345, "Europe/Moscow"
        )
        mock_message.answer.assert_called_once_with(
            "Временная зона успешно изменена!", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_change_timezone_invalid_format(self):
        """Test timezone change with invalid format"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.text = "/change_timezone"
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_deadline_service = AsyncMock()

        await change_timezone_command(mock_message, mock_deadline_service)

        mock_deadline_service.edit_timezone.assert_not_called()
        mock_message.answer.assert_called_once_with(
            "Неверный формат команды!", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_change_timezone_failure(self):
        """Test timezone change failure"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.text = "/change_timezone Invalid/Zone"
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_deadline_service = AsyncMock()
        mock_deadline_service.edit_timezone.return_value = False

        await change_timezone_command(mock_message, mock_deadline_service)

        mock_deadline_service.edit_timezone.assert_called_once_with(
            12345, "Invalid/Zone"
        )
        mock_message.answer.assert_called_once_with(
            "Неверная временная зона!", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_delete_deadline_command_with_deadlines(self):
        """Test delete command with existing deadlines"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_deadline_service = AsyncMock()
        mock_deadline = Mock()
        mock_deadline.id = 1
        mock_deadline.title = "Test Deadline"
        mock_deadline.deadline_at = datetime.now(timezone.utc) + timedelta(days=7)
        mock_deadline_service.list_for_user.return_value = [mock_deadline]

        await delete_deadline_command(mock_message, mock_deadline_service)

        mock_deadline_service.list_for_user.assert_called_once_with(12345)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert call_args[0][0] == "\n".join(
            [
                "Выбери дедлайн для удаления:",
                " ",
                "1. ⏰ Test Deadline - " + str(mock_deadline.deadline_at),
            ]
        )
        assert call_args[1]["reply_markup"] is not None
        assert call_args[1]["parse_mode"] == "Markdown"

    @pytest.mark.asyncio
    async def test_delete_deadline_command_no_deadlines(self):
        """Test delete command with no deadlines"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_deadline_service = AsyncMock()
        mock_deadline_service.list_for_user.return_value = []

        await delete_deadline_command(mock_message, mock_deadline_service)

        mock_deadline_service.list_for_user.assert_called_once_with(12345)
        mock_message.answer.assert_called_once_with(
            "Нет дедлайнов для удаления!", parse_mode="Markdown"
        )

    @pytest.mark.asyncio
    async def test_add_title_handler(self):
        """Test adding title in FSM"""
        mock_message = Mock(spec=Message)
        mock_message.text = "Test Title"
        mock_message.answer = AsyncMock()
        mock_state = Mock(spec=FSMContext)
        mock_state.update_data = AsyncMock()
        mock_state.set_state = AsyncMock()

        await add_title(mock_message, mock_state)

        mock_state.update_data.assert_called_once_with(title="Test Title")
        mock_message.answer.assert_called_once_with(
            "Введи дату в формате ДД.ММ.ГГГГ ЧЧ:ММ", parse_mode="Markdown"
        )
        mock_state.set_state.assert_called_once_with(AddDeadlineFSM.datetime)

    @pytest.mark.asyncio
    async def test_add_datetime_success(self):
        """Test successful datetime addition in FSM"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.text = "25.12.2025 15:00"
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_state = Mock(spec=FSMContext)
        mock_state.get_data = AsyncMock(return_value={"title": "Test Title"})
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline_service.create = AsyncMock()

        with patch("handlers.base_handlers.dateparser.parse") as mock_parse:
            parsed_date = datetime(2025, 12, 25, 15, 0, tzinfo=timezone.utc)
            mock_parse.return_value = parsed_date

            await add_datetime(mock_message, mock_state, mock_deadline_service)

        mock_deadline_service.create.assert_called_once_with(
            user_id=12345, title="Test Title", dt=parsed_date
        )
        mock_message.answer.assert_called_once()
        assert "Дедлайн успешно добавлен!" in mock_message.answer.call_args[0][0]
        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_datetime_invalid_date(self):
        """Test invalid date in datetime handler"""
        mock_user = Mock(spec=TelegramUser)
        mock_user.id = 12345
        mock_message = Mock(spec=Message)
        mock_message.text = "invalid date"
        mock_message.answer = AsyncMock()
        mock_message.from_user = mock_user

        mock_state = Mock(spec=FSMContext)
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()

        with patch("handlers.base_handlers.dateparser.parse") as mock_parse:
            mock_parse.return_value = None

            await add_datetime(mock_message, mock_state, mock_deadline_service)

        mock_deadline_service.create.assert_not_called()
        mock_message.answer.assert_called_once_with(
            "Не понял дату(", parse_mode="Markdown"
        )
        mock_state.clear.assert_not_called()
