from unittest.mock import AsyncMock, Mock

import pytest
from aiogram.types import Message

from handlers.start_router import start


class TestStartRouter:
    """Test cases for start router handlers"""

    @pytest.mark.asyncio
    async def test_start_command(self):
        """Test start command handler"""
        mock_message = Mock(spec=Message)
        mock_message.answer = AsyncMock()

        await start(mock_message)

        mock_message.answer.assert_called_once_with(
            "Welcome to the deadline bot!", parse_mode="Markdown"
        )
