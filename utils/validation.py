"""
Input validation utilities
"""

import re
from typing import Optional

from pydantic import BaseModel, StrictInt, field_validator


class TelegramUserValidation(BaseModel):
    """Schema for validating Telegram user data"""

    user_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    is_bot: bool = False

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        """Validate user ID is positive integer"""
        if not isinstance(v, int) or v <= 0:
            raise ValueError("Invalid user ID")
        return v

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        """Validate username format"""
        if v is not None:
            if not re.match(r"^[a-zA-Z0-9_]{3,32}$", v):
                raise ValueError("Invalid username format")
        return v

    @field_validator("is_bot")
    @classmethod
    def validate_is_bot(cls, v):
        """Ensure user is not a bot"""
        if v:
            raise ValueError("Bots are not allowed")
        return v


class DeadlineInputValidation(BaseModel):
    """Schema for validating deadline input"""

    title: str
    description: Optional[str] = None
    due_date: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, v):
        """Validate deadline title"""
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        if len(v) > 200:
            raise ValueError("Title too long (max 200 characters)")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v):
        """Validate deadline description"""
        if v is not None:
            if len(v) > 1000:
                raise ValueError("Description too long (max 1000 characters)")
        return v

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v):
        """Basic validation for due date string"""
        if not v or not v.strip():
            raise ValueError("Due date cannot be empty")
        return v.strip()


class NotificationSettingsValidation(BaseModel):
    """Schema for validating notification settings"""

    enabled: bool = True
    advance_hours: StrictInt = 24

    @field_validator("advance_hours")
    @classmethod
    def validate_advance_hours(cls, v):
        """Validate advance notification hours"""
        if not isinstance(v, int) or v < 0 or v > 168:  # Max 1 week
            raise ValueError("Advance hours must be between 0 and 168")
        return v


def validate_telegram_user(user_data: dict) -> TelegramUserValidation:
    """Validate Telegram user data"""
    return TelegramUserValidation(**user_data)


def validate_deadline_input(
    title: str, description: Optional[str], due_date: str
) -> DeadlineInputValidation:
    """Validate deadline input data"""
    return DeadlineInputValidation(
        title=title, description=description, due_date=due_date
    )


def validate_notification_settings(
    enabled: bool, advance_hours: int
) -> NotificationSettingsValidation:
    """Validate notification settings"""
    return NotificationSettingsValidation(enabled=enabled, advance_hours=advance_hours)


def sanitize_text(text: str, max_length: int = 1000) -> str:
    """Sanitize text input to prevent injection attacks"""
    if not text:
        return ""
    # Limit length
    if len(text) > max_length:
        text = text[: max_length - 3] + "..."

    return text.strip()
