import pytest

from utils.validation import (
    DeadlineInputValidation,
    NotificationSettingsValidation,
    TelegramUserValidation,
    sanitize_text,
    validate_deadline_input,
    validate_notification_settings,
    validate_telegram_user,
)


class TestTelegramUserValidation:
    """Test suite for Telegram user validation"""

    def test_valid_user_data(self):
        """Test valid user data"""
        data = {
            "user_id": 12345,
            "first_name": "John",
            "username": "johndoe",
            "is_bot": False,
        }

        result = TelegramUserValidation(**data)

        assert result.user_id == 12345
        assert result.first_name == "John"
        assert result.username == "johndoe"
        assert result.is_bot is False

    def test_valid_user_minimal_data(self):
        """Test minimal valid user data"""
        data = {"user_id": 12345, "is_bot": False}

        result = TelegramUserValidation(**data)

        assert result.user_id == 12345
        assert result.first_name is None
        assert result.username is None
        assert result.is_bot is False

    def test_invalid_user_id(self):
        """Test invalid user ID"""
        data = {"user_id": -1, "is_bot": False}

        with pytest.raises(ValueError, match="Invalid user ID"):
            TelegramUserValidation(**data)

    def test_invalid_user_id_type(self):
        """Test invalid user ID type"""
        data = {"user_id": -12345, "is_bot": False}

        with pytest.raises(ValueError, match="Invalid user ID"):
            TelegramUserValidation(**data)

    def test_user_is_bot(self):
        """Test bot user"""
        data = {"user_id": 12345, "is_bot": True}

        with pytest.raises(ValueError, match="Bots are not allowed"):
            TelegramUserValidation(**data)

    def test_invalid_username(self):
        """Test invalid username"""
        data = {"user_id": 12345, "username": "invalid username!", "is_bot": False}

        with pytest.raises(ValueError, match="Invalid username format"):
            TelegramUserValidation(**data)


class TestDeadlineInputValidation:
    """Test suite for deadline input validation"""

    def test_valid_deadline_input(self):
        """Test valid deadline input"""
        data = {
            "title": "Test Deadline",
            "description": "Test Description",
            "due_date": "2024-12-31 23:59",
        }

        result = DeadlineInputValidation(**data)

        assert result.title == "Test Deadline"
        assert result.description == "Test Description"
        assert result.due_date == "2024-12-31 23:59"

    def test_minimal_deadline_input(self):
        """Test minimal deadline input"""
        data = {"title": "Test", "due_date": "2024-12-31 23:59"}

        result = DeadlineInputValidation(**data)

        assert result.title == "Test"
        assert result.description is None
        assert result.due_date == "2024-12-31 23:59"

    def test_empty_title(self):
        """Test empty title"""
        data = {"title": "", "due_date": "2024-12-31 23:59"}

        with pytest.raises(ValueError, match="Title cannot be empty"):
            DeadlineInputValidation(**data)

    def test_title_too_long(self):
        """Test title too long"""
        data = {"title": "x" * 201, "due_date": "2024-12-31 23:59"}

        with pytest.raises(ValueError, match="Title too long"):
            DeadlineInputValidation(**data)

    def test_title_with_whitespace(self):
        """Test title with only whitespace"""
        data = {"title": "   ", "due_date": "2024-12-31 23:59"}

        with pytest.raises(ValueError, match="Title cannot be empty"):
            DeadlineInputValidation(**data)

    def test_empty_due_date(self):
        """Test empty due date"""
        data = {"title": "Test", "due_date": ""}

        with pytest.raises(ValueError, match="Due date cannot be empty"):
            DeadlineInputValidation(**data)

    def test_description_too_long(self):
        """Test description too long"""
        data = {
            "title": "Test",
            "description": "x" * 1001,
            "due_date": "2024-12-31 23:59",
        }

        with pytest.raises(ValueError, match="Description too long"):
            DeadlineInputValidation(**data)


class TestNotificationSettingsValidation:
    """Test suite for notification settings validation"""

    def test_valid_notification_settings(self):
        """Test valid notification settings"""
        data = {"enabled": True, "advance_hours": 24}

        result = NotificationSettingsValidation(**data)

        assert result.enabled is True
        assert result.advance_hours == 24

    def test_valid_advance_hours_range(self):
        """Test valid advance hours range"""
        for hours in [0, 1, 24, 168]:
            data = {"enabled": True, "advance_hours": hours}

            result = NotificationSettingsValidation(**data)
            assert result.advance_hours == hours

    def test_invalid_advance_hours_negative(self):
        """Test negative advance hours"""
        data = {"enabled": True, "advance_hours": -1}

        with pytest.raises(ValueError, match="Advance hours must be between 0 and 168"):
            NotificationSettingsValidation(**data)

    def test_invalid_advance_hours_too_large(self):
        """Test advance hours too large"""
        data = {"enabled": True, "advance_hours": 169}

        with pytest.raises(ValueError, match="Advance hours must be between 0 and 168"):
            NotificationSettingsValidation(**data)

    def test_invalid_advance_hours_type(self):
        """Test invalid advance hours type"""
        data = {"enabled": True, "advance_hours": "24"}

        with pytest.raises(ValueError):
            NotificationSettingsValidation(**data)


class TestValidationFunctions:
    """Test suite for validation functions"""

    def test_validate_telegram_user_success(self):
        """Test successful user validation"""
        data = {"user_id": 12345, "first_name": "John", "is_bot": False}

        result = validate_telegram_user(data)

        assert isinstance(result, TelegramUserValidation)
        assert result.user_id == 12345

    def test_validate_deadline_input_success(self):
        """Test successful deadline input validation"""
        result = validate_deadline_input(
            title="Test Deadline",
            description="Test Description",
            due_date="2024-12-31 23:59",
        )

        assert isinstance(result, DeadlineInputValidation)
        assert result.title == "Test Deadline"
        assert result.description == "Test Description"

    def test_validate_notification_settings_success(self):
        """Test successful notification settings validation"""
        result = validate_notification_settings(enabled=True, advance_hours=24)

        assert isinstance(result, NotificationSettingsValidation)
        assert result.enabled is True
        assert result.advance_hours == 24

    def test_sanitize_text_normal(self):
        """Test text sanitization with normal text"""
        text = "Hello, World!"
        result = sanitize_text(text)

        assert result == "Hello, World!"

    def test_sanitize_text_too_long(self):
        """Test text sanitization with too long text"""
        text = "x" * 100
        result = sanitize_text(text, max_length=50)

        assert len(result) == 50
        assert result.endswith("...")

    def test_sanitize_text_empty(self):
        """Test text sanitization with empty text"""
        result = sanitize_text("")

        assert result == ""


class TestValidationIntegration:
    """Integration tests for validation functions"""

    def test_deadline_workflow_validation(self):
        """Test complete deadline creation workflow validation"""
        user_data = {"user_id": 12345, "first_name": "John", "is_bot": False}

        deadline_data = validate_deadline_input(
            title="Important Deadline",
            description="This is an important deadline",
            due_date="2024-12-31 23:59",
        )

        assert validate_telegram_user(user_data) is not None
        assert deadline_data.title == "Important Deadline"
        assert deadline_data.description == "This is an important deadline"
        assert deadline_data.due_date == "2024-12-31 23:59"

    def test_notification_settings_workflow_validation(self):
        """Test notification settings workflow validation"""
        settings = validate_notification_settings(
            enabled=True,
            advance_hours=48,  # 2 days
        )

        assert settings.enabled is True
        assert settings.advance_hours == 48
