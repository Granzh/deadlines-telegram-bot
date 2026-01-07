from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Message

from handlers.help import HELP_TEXT, help_handler


class TestHelpHandler:
    """Test cases for help handler"""

    @pytest.mark.asyncio
    async def test_help_command(self):
        """Test help command handler"""
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        await help_handler(mock_message)

        mock_message.answer.assert_called_once_with(HELP_TEXT, parse_mode="Markdown")

    def test_help_text_content(self):
        """Test that HELP_TEXT contains expected content"""
        assert "/start" in HELP_TEXT
        assert "/help" in HELP_TEXT
        assert "/add" in HELP_TEXT
        assert "/list" in HELP_TEXT
        assert "/edit" in HELP_TEXT
        assert "/delete" in HELP_TEXT
        assert "/notifications" in HELP_TEXT
