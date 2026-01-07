from datetime import datetime, timezone
from unittest.mock import AsyncMock, Mock, patch

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InaccessibleMessage,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from handlers.edit_deadline import (
    choose_edit_field,
    edit_deadline_command,
    process_field_choice,
    process_new_datetime,
    process_new_title,
)
from handlers.fsm_edit_deadline import EditDeadlineFSM


class TestEditDeadlineHandlers:
    """Test cases for edit deadline handlers"""

    @pytest.mark.asyncio
    async def test_edit_deadline_command_with_deadlines(self):
        """Test edit command with existing deadlines"""
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 12345

        mock_deadline_service = AsyncMock()
        mock_deadline = Mock()
        mock_deadline.id = 1
        mock_deadline.title = "Test Deadline"
        mock_deadline.deadline_at = datetime.now(timezone.utc)
        mock_deadline_service.list_for_user.return_value = [mock_deadline]

        await edit_deadline_command(mock_message, mock_deadline_service)

        mock_deadline_service.list_for_user.assert_called_once_with(12345)
        mock_message.answer.assert_called_once()
        call_args = mock_message.answer.call_args
        assert "Выбери дедлайн для редактирования:" in call_args[0][0]
        assert call_args[1]["reply_markup"] is not None

    @pytest.mark.asyncio
    async def test_edit_deadline_command_no_deadlines(self):
        """Test edit command with no deadlines"""
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 12345

        mock_deadline_service = AsyncMock()
        mock_deadline_service.list_for_user.return_value = []

        await edit_deadline_command(mock_message, mock_deadline_service)

        mock_deadline_service.list_for_user.assert_called_once_with(12345)
        mock_message.answer.assert_called_once_with(
            "У вас нет дедлайнов для редактирования!"
        )

    @pytest.mark.asyncio
    async def test_choose_edit_field_success(self):
        """Test choosing edit field successfully"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "edit:123"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 456
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.edit_text = AsyncMock()

        mock_state = Mock(spec=FSMContext)
        mock_state.update_data = AsyncMock()
        mock_state.set_state = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline = Mock()
        mock_deadline.title = "Test Deadline"
        mock_deadline.deadline_at = datetime.now(timezone.utc)
        mock_deadline_service.get_by_id.return_value = mock_deadline

        await choose_edit_field(mock_callback, mock_state, mock_deadline_service)

        mock_deadline_service.get_by_id.assert_called_once_with(123, 456)
        mock_state.update_data.assert_called_once_with(deadline_id=123)
        mock_callback.message.edit_text.assert_called_once()
        mock_state.set_state.assert_called_once_with(EditDeadlineFSM.choose_field)
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_choose_edit_field_invalid_callback_data(self):
        """Test choosing edit field with invalid callback data"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "invalid"
        mock_callback.answer = AsyncMock(show_alert=True)

        mock_state = Mock(spec=FSMContext)
        mock_deadline_service = AsyncMock()

        await choose_edit_field(mock_callback, mock_state, mock_deadline_service)

        mock_deadline_service.get_by_id.assert_not_called()
        mock_callback.answer.assert_called_once_with(
            "Invalid deadline ID", show_alert=True
        )

    @pytest.mark.asyncio
    async def test_choose_edit_field_deadline_not_found(self):
        """Test choosing edit field when deadline not found"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "edit:123"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 456
        mock_callback.answer = AsyncMock(show_alert=True)

        mock_state = Mock(spec=FSMContext)
        mock_deadline_service = AsyncMock()
        mock_deadline_service.get_by_id.return_value = None

        await choose_edit_field(mock_callback, mock_state, mock_deadline_service)

        mock_deadline_service.get_by_id.assert_called_once_with(123, 456)
        mock_callback.answer.assert_called_once_with(
            "Deadline not found", show_alert=True
        )

    @pytest.mark.asyncio
    async def test_choose_edit_field_inaccessible_message(self):
        """Test choosing edit field with inaccessible message"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "edit:123"
        mock_callback.from_user = Mock()
        mock_callback.from_user.id = 456
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock(spec=InaccessibleMessage)

        mock_state = Mock(spec=FSMContext)
        mock_state.update_data = AsyncMock()
        mock_state.set_state = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline = Mock()
        mock_deadline.title = "Test Deadline"
        mock_deadline.deadline_at = datetime.now(timezone.utc)
        mock_deadline_service.get_by_id.return_value = mock_deadline

        await choose_edit_field(mock_callback, mock_state, mock_deadline_service)

        mock_deadline_service.get_by_id.assert_called_once_with(123, 456)
        mock_state.update_data.assert_called_once_with(deadline_id=123)
        mock_state.set_state.assert_called_once_with(EditDeadlineFSM.choose_field)
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_field_choice_cancel(self):
        """Test canceling field choice"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "edit_field:cancel"
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.edit_text = AsyncMock()

        mock_state = Mock(spec=FSMContext)
        mock_state.clear = AsyncMock()

        await process_field_choice(mock_callback, mock_state)

        mock_state.clear.assert_called_once()
        mock_callback.message.edit_text.assert_called_once_with(
            "Редактирование отменено", parse_mode="Markdown"
        )
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_field_choice_title(self):
        """Test choosing to edit title"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "edit_field:title"
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.edit_text = AsyncMock()

        mock_state = Mock(spec=FSMContext)
        mock_state.set_state = AsyncMock()

        await process_field_choice(mock_callback, mock_state)

        mock_callback.message.edit_text.assert_called_once_with(
            "Введи новое название дедлайна:", parse_mode="Markdown"
        )
        mock_state.set_state.assert_called_once_with(EditDeadlineFSM.edit_title)
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_field_choice_datetime(self):
        """Test choosing to edit datetime"""
        mock_callback = Mock(spec=CallbackQuery)
        mock_callback.data = "edit_field:datetime"
        mock_callback.answer = AsyncMock()
        mock_callback.message = Mock()
        mock_callback.message.edit_text = AsyncMock()

        mock_state = Mock(spec=FSMContext)
        mock_state.set_state = AsyncMock()

        await process_field_choice(mock_callback, mock_state)

        mock_callback.message.edit_text.assert_called_once_with(
            "Введи новую дату", parse_mode="Markdown"
        )
        mock_state.set_state.assert_called_once_with(EditDeadlineFSM.edit_datetime)
        mock_callback.answer.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_new_title_success(self):
        """Test processing new title successfully"""
        mock_message = Mock(spec=Message)
        mock_message.text = "New Title"
        mock_message.answer = AsyncMock()

        mock_state = Mock(spec=FSMContext)
        mock_state.get_data = AsyncMock(return_value={"deadline_id": 123})
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline_service.update.return_value = True

        await process_new_title(mock_message, mock_state, mock_deadline_service)

        mock_state.get_data.assert_called_once()
        mock_deadline_service.update.assert_called_once_with(123, title="New Title")
        mock_message.answer.assert_called_once_with(
            "Название успешно изменено на: *New Title*", parse_mode="Markdown"
        )
        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_new_title_no_deadline_id(self):
        """Test processing new title with no deadline ID"""
        mock_message = Mock(spec=Message)
        mock_message.text = "New Title"
        mock_message.answer = AsyncMock()

        mock_state = Mock(spec=FSMContext)
        mock_state.get_data = AsyncMock(return_value={})
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()

        await process_new_title(mock_message, mock_state, mock_deadline_service)

        mock_deadline_service.update.assert_not_called()
        mock_message.answer.assert_called_once_with(
            "Ошибка: дедлайн не найден", parse_mode="Markdown"
        )
        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_new_title_update_failure(self):
        """Test processing new title with update failure"""
        mock_message = Mock(spec=Message)
        mock_message.text = "New Title"
        mock_message.answer = AsyncMock()

        mock_state = Mock(spec=FSMContext)
        mock_state.get_data = AsyncMock(return_value={"deadline_id": 123})
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline_service.update.return_value = False

        await process_new_title(mock_message, mock_state, mock_deadline_service)

        mock_deadline_service.update.assert_called_once_with(123, title="New Title")
        mock_message.answer.assert_called_once_with(
            "Не удалось обновить дедлайн", parse_mode="Markdown"
        )
        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_new_datetime_success(self):
        """Test processing new datetime successfully"""
        mock_message = Mock(spec=Message)
        mock_message.text = "25.12.2025 15:00"
        mock_message.answer = AsyncMock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 456

        mock_state = Mock(spec=FSMContext)
        mock_state.get_data = AsyncMock(return_value={"deadline_id": 123})
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()
        mock_deadline_service.update.return_value = True

        with patch("handlers.edit_deadline.dateparser.parse") as mock_parse:
            parsed_date = datetime(2025, 12, 25, 15, 0)
            mock_parse.return_value = parsed_date

            await process_new_datetime(mock_message, mock_state, mock_deadline_service)

        expected_dt = parsed_date.replace(tzinfo=timezone.utc)
        mock_deadline_service.update.assert_called_once_with(123, dt=expected_dt)
        mock_message.answer.assert_called_once()
        assert "Дата успешно изменена на" in mock_message.answer.call_args[0][0]
        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_new_datetime_invalid_date(self):
        """Test processing new datetime with invalid date"""
        mock_message = Mock(spec=Message)
        mock_message.text = "invalid date"
        mock_message.answer = AsyncMock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 456

        mock_state = Mock(spec=FSMContext)
        mock_state.get_data = AsyncMock(return_value={"deadline_id": 123})
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()

        with patch("handlers.edit_deadline.dateparser.parse") as mock_parse:
            mock_parse.return_value = None

            await process_new_datetime(mock_message, mock_state, mock_deadline_service)

        mock_deadline_service.update.assert_not_called()
        mock_message.answer.assert_called_once_with(
            "Не понял дату(", parse_mode="Markdown"
        )
        mock_state.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_new_datetime_no_deadline_id(self):
        """Test processing new datetime with no deadline ID"""
        mock_message = Mock(spec=Message)
        mock_message.text = "25.12.2025 15:00"
        mock_message.answer = AsyncMock()
        mock_message.from_user = Mock()
        mock_message.from_user.id = 456

        mock_state = Mock(spec=FSMContext)
        mock_state.get_data = AsyncMock(return_value={})
        mock_state.clear = AsyncMock()

        mock_deadline_service = AsyncMock()

        await process_new_datetime(mock_message, mock_state, mock_deadline_service)

        mock_deadline_service.update.assert_not_called()
        mock_message.answer.assert_called_once_with(
            "Ошибка: дедлайн не найден", parse_mode="Markdown"
        )
        mock_state.clear.assert_called_once()
