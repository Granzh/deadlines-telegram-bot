from datetime import datetime, timezone

from exceptions import (
    CallbackDataError,
    InvalidDeadlineError,
    InvalidTimezoneError,
    ValidationError,
)
from utils.error_messages import (
    EXCEPTION_FORMATTERS,
    format_callback_error,
    format_deadline_error,
    format_exception_message,
    format_validation_error,
    get_error_message,
    get_help_message,
    get_success_message,
    get_validation_message,
)


class TestErrorMessages:
    """Test error message utilities"""

    def test_get_error_message_basic(self):
        """Test getting basic error message"""
        message = get_error_message("general_error")
        assert message == "Произошла ошибка. Попробуйте позже."

    def test_get_error_message_with_formatting(self):
        """Test getting error message with formatting"""
        message = get_error_message("too_long_input", max_length=200)
        assert message == "Слишком длинный текст. Максимальная длина: 200 символов."

    def test_get_error_message_unknown_type(self):
        """Test getting message for unknown error type"""
        message = get_error_message("unknown_error")
        assert message == "Произошла ошибка. Попробуйте позже."

    def test_get_success_message_basic(self):
        """Test getting basic success message"""
        message = get_success_message("deadline_created")
        assert message == "✅ Дедлайн успешно создан!"

    def test_get_success_message_with_formatting(self):
        """Test getting success message with formatting"""
        message = get_success_message("deadline_created", title="Test")
        # Should not fail even with unused formatting
        assert "✅ Дедлайн успешно создан!" in message

    def test_get_success_message_unknown_type(self):
        """Test getting message for unknown success type"""
        message = get_success_message("unknown_success")
        assert message == "Операция выполнена успешно!"

    def test_get_help_message_basic(self):
        """Test getting basic help message"""
        message = get_help_message("no_deadlines")
        assert message == "У вас нет дедлайнов."

    def test_get_help_message_with_formatting(self):
        """Test getting help message with formatting"""
        message = get_help_message("title_too_long", max_length=200)
        assert message == "Название слишком длинное (макс. 200 символов)."

    def test_get_help_message_unknown_type(self):
        """Test getting message for unknown help type"""
        message = get_help_message("unknown_help")
        assert message == ""

    def test_get_validation_message_basic(self):
        """Test getting basic validation message"""
        message = get_validation_message("title_required")
        assert message == "Название дедлайна обязательно."

    def test_get_validation_message_with_formatting(self):
        """Test getting validation message with formatting"""
        message = get_validation_message("timezone_invalid", timezone="Europe/Moscow")
        assert message == "Неверный часовой пояс. Пример: Europe/Moscow."

    def test_get_validation_message_unknown_type(self):
        """Test getting message for unknown validation type"""
        message = get_validation_message("unknown_validation")
        assert message == "Ошибка валидации."


class TestErrorFormatters:
    """Test error message formatters"""

    def test_format_deadline_error(self):
        """Test formatting deadline error"""
        past_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        error = InvalidDeadlineError(past_date)

        message = format_deadline_error(error)

        assert "Дедлайн не может быть в прошлом" in message

    def test_format_deadline_error_no_deadline_attr(self):
        """Test formatting deadline error without deadline_at attribute (covers line 113)"""
        error = ValidationError("Some deadline error")

        message = format_deadline_error(error)

        # Should fallback to general deadline create error
        assert message == get_error_message("deadline_create_error")

    def test_format_validation_error_empty(self):
        """Test formatting validation error - empty input"""
        error = ValidationError("Title cannot be empty")

        message = format_validation_error(error)

        assert message == "Поле не может быть пустым."

    def test_format_validation_error_long(self):
        """Test formatting validation error - too long"""
        error = ValidationError("Title too long")

        message = format_validation_error(error)

        assert "Слишком длинный текст" in message
        assert "200" in message

    def test_format_validation_error_date(self):
        """Test formatting validation error - date"""
        error = ValidationError("Invalid date format")

        message = format_validation_error(error)

        assert message == get_error_message("invalid_date")

    def test_format_validation_error_timezone(self):
        """Test formatting validation error - timezone"""
        error = ValidationError("Invalid timezone")

        message = format_validation_error(error)

        assert message == get_error_message("invalid_timezone")

    def test_format_validation_error_generic(self):
        """Test formatting validation error - generic"""
        error = ValidationError("Some other validation error")

        message = format_validation_error(error)

        assert message == get_error_message(
            "validation_error", details="Some other validation error"
        )

    def test_format_callback_error(self):
        """Test formatting callback error"""
        error = CallbackDataError("invalid:data")

        message = format_callback_error(error)

        assert message == get_error_message(
            "invalid_callback_data", data="invalid:data"
        )

    def test_format_callback_error_no_callback_data_attr(self):
        """Test formatting callback error without callback_data attribute (covers line 134)"""
        error = Exception("Some error without callback_data")

        message = format_callback_error(error)

        # Should fallback to general invalid callback data message
        assert message == get_error_message("invalid_callback_data")

    def test_format_exception_message_known_type(self):
        """Test formatting exception for known type"""
        error = InvalidTimezoneError("Invalid/Zone")

        message = format_exception_message(error)

        assert message == get_error_message("invalid_timezone")

    def test_format_exception_message_unknown_type(self):
        """Test formatting exception for unknown type"""
        error = ValueError("Some random error")

        message = format_exception_message(error)

        assert message == get_error_message("general_error")

    def test_exception_formatters_coverage(self):
        """Test that all exception types have formatters"""
        expected_formatters = {
            "InvalidDeadlineError",
            "ValidationError",
            "CallbackDataError",
            "InvalidTimezoneError",
            "InvalidDateError",
            "DeadlineNotFoundError",
            "DatabaseError",
            "NotificationError",
        }

        actual_formatters = set(EXCEPTION_FORMATTERS.keys())
        assert actual_formatters == expected_formatters

    def test_each_formatter_callable(self):
        """Test that all formatters are callable"""
        for exception_type, formatter in EXCEPTION_FORMATTERS.items():
            assert callable(formatter), (
                f"Formatter for {exception_type} is not callable"
            )

    def test_formatters_return_strings(self):
        """Test that all formatters return strings"""
        test_errors = [
            InvalidDeadlineError(datetime.now()),
            ValidationError("Test"),
            CallbackDataError("test"),
            InvalidTimezoneError("UTC"),
        ]

        for error in test_errors:
            exception_type = type(error).__name__
            if exception_type in EXCEPTION_FORMATTERS:
                formatter = EXCEPTION_FORMATTERS[exception_type]
                message = formatter(error)
                assert isinstance(message, str), (
                    f"Formatter for {exception_type} didn't return string"
                )
                assert len(message) > 0, (
                    f"Formatter for {exception_type} returned empty string"
                )


class TestMessageConstants:
    """Test that all message constants are present"""

    def test_error_messages_completeness(self):
        """Test that all required error messages exist"""
        from utils.error_messages import ERROR_MESSAGES

        required_keys = [
            "general_error",
            "validation_error",
            "database_error",
            "deadline_not_found",
            "deadline_create_error",
            "deadline_update_error",
            "deadline_delete_error",
            "deadline_in_past",
            "deadline_empty_title",
            "invalid_timezone",
            "invalid_date",
            "invalid_callback_data",
            "invalid_deadline_id",
            "notification_error",
            "empty_input",
            "too_long_input",
            "invalid_number",
            "rate_limit",
            "unknown_command",
            "unknown_message",
            "file_not_found",
            "permission_denied",
            "network_error",
            "timeout_error",
        ]

        for key in required_keys:
            assert key in ERROR_MESSAGES, f"Missing error message: {key}"
            assert isinstance(ERROR_MESSAGES[key], str), (
                f"Error message {key} is not a string"
            )
            assert len(ERROR_MESSAGES[key]) > 0, f"Error message {key} is empty"

    def test_success_messages_completeness(self):
        """Test that all required success messages exist"""
        from utils.error_messages import SUCCESS_MESSAGES

        required_keys = [
            "deadline_created",
            "deadline_updated",
            "deadline_deleted",
            "timezone_updated",
            "notifications_enabled",
            "notifications_disabled",
            "settings_saved",
        ]

        for key in required_keys:
            assert key in SUCCESS_MESSAGES, f"Missing success message: {key}"
            assert isinstance(SUCCESS_MESSAGES[key], str), (
                f"Success message {key} is not a string"
            )
            assert len(SUCCESS_MESSAGES[key]) > 0, f"Success message {key} is empty"

    def test_help_messages_completeness(self):
        """Test that all required help messages exist"""
        from utils.error_messages import HELP_MESSAGES

        required_keys = [
            "no_deadlines",
            "no_deadlines_to_edit",
            "choose_deadline",
            "enter_title",
            "enter_date",
            "enter_timezone",
            "deadline_saved",
        ]

        for key in required_keys:
            assert key in HELP_MESSAGES, f"Missing help message: {key}"
            assert isinstance(HELP_MESSAGES[key], str), (
                f"Help message {key} is not a string"
            )
            assert len(HELP_MESSAGES[key]) > 0, f"Help message {key} is empty"

    def test_validation_messages_completeness(self):
        """Test that all required validation messages exist"""
        from utils.error_messages import VALIDATION_MESSAGES

        required_keys = [
            "title_required",
            "title_too_long",
            "date_required",
            "date_invalid",
            "date_past",
            "timezone_required",
            "timezone_invalid",
        ]

        for key in required_keys:
            assert key in VALIDATION_MESSAGES, f"Missing validation message: {key}"
            assert isinstance(VALIDATION_MESSAGES[key], str), (
                f"Validation message {key} is not a string"
            )
            assert len(VALIDATION_MESSAGES[key]) > 0, (
                f"Validation message {key} is empty"
            )


class TestMessageFormatting:
    """Test message formatting behavior"""

    def test_message_formatting_with_missing_args(self):
        """Test that formatting doesn't fail with missing args"""
        message = get_error_message("too_long_input")
        # Should not fail even without max_length
        assert "Слишком длинный текст" in message

    def test_message_formatting_with_extra_args(self):
        """Test that formatting works with extra args"""
        message = get_success_message("deadline_created", extra_arg="ignored")
        assert "✅ Дедлайн успешно создан!" in message

    def test_message_consistency(self):
        """Test that messages are consistent"""
        error_msg = get_error_message("general_error")
        success_msg = get_success_message("deadline_created")

        assert isinstance(error_msg, str)
        assert isinstance(success_msg, str)
        assert len(error_msg) > 0
        assert len(success_msg) > 0

    def test_russian_language_messages(self):
        """Test that messages are in Russian"""
        from utils.error_messages import ERROR_MESSAGES

        for key, message in ERROR_MESSAGES.items():
            # Check that messages contain Cyrillic characters for user-facing errors
            if key not in ["file_not_found", "permission_denied"]:  # System errors
                assert any(ord(char) > 127 for char in message) or message in [
                    "Произошла ошибка. Попробуйте позже.",
                    "Ошибка базы данных. Попробуйте позже.",
                ], f"Message {key} might not be in Russian: {message}"
