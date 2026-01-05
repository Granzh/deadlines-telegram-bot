from datetime import datetime

import pytest

from exceptions import (
    CallbackDataError,
    DatabaseError,
    DeadlineBotError,
    DeadlineCreationError,
    DeadlineDeletionError,
    DeadlineNotFoundError,
    DeadlineUpdateError,
    InvalidDateError,
    InvalidDeadlineError,
    InvalidTimezoneError,
    NotificationError,
    TimezoneConversionError,
    ValidationError,
)


class TestDeadlineBotError:
    """Test base exception class"""

    def test_deadline_bot_error_inheritance(self):
        """Test that DeadlineBotError inherits from Exception"""
        error = DeadlineBotError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert str(error) == "Test error"

    def test_deadline_bot_error_no_message(self):
        """Test DeadlineBotError without message"""
        error = DeadlineBotError()
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)


class TestDatabaseError:
    """Test DatabaseError exception"""

    def test_database_error_inheritance(self):
        """Test that DatabaseError inherits from DeadlineBotError"""
        error = DatabaseError("Database error")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, DatabaseError)
        assert str(error) == "Database error"


class TestDeadlineNotFoundError:
    """Test DeadlineNotFoundError exception"""

    def test_deadline_not_found_error_properties(self):
        """Test DeadlineNotFoundError properties"""
        error = DeadlineNotFoundError(123)
        assert error.deadline_id == 123
        assert str(error) == "Deadline with id 123 not found"
        assert isinstance(error, DatabaseError)

    def test_deadline_not_found_error_inheritance(self):
        """Test inheritance chain"""
        error = DeadlineNotFoundError(456)
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, DatabaseError)
        assert isinstance(error, DeadlineNotFoundError)


class TestValidationError:
    """Test ValidationError exception"""

    def test_validation_error_inheritance(self):
        """Test that ValidationError inherits from DeadlineBotError"""
        error = ValidationError("Validation failed")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, ValidationError)
        assert str(error) == "Validation failed"


class TestInvalidTimezoneError:
    """Test InvalidTimezoneError exception"""

    def test_invalid_timezone_error_properties(self):
        """Test InvalidTimezoneError properties"""
        error = InvalidTimezoneError("Invalid/Timezone")
        assert error.timezone == "Invalid/Timezone"
        assert str(error) == "Invalid timezone: Invalid/Timezone"
        assert isinstance(error, ValidationError)

    def test_invalid_timezone_error_inheritance(self):
        """Test inheritance chain"""
        error = InvalidTimezoneError("Mars/Phobos")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, ValidationError)
        assert isinstance(error, InvalidTimezoneError)


class TestInvalidDateError:
    """Test InvalidDateError exception"""

    def test_invalid_date_error_properties(self):
        """Test InvalidDateError properties"""
        error = InvalidDateError("32.13.2025")
        assert error.date_str == "32.13.2025"
        assert str(error) == "Cannot parse date: 32.13.2025"
        assert isinstance(error, ValidationError)

    def test_invalid_date_error_inheritance(self):
        """Test inheritance chain"""
        error = InvalidDateError("invalid date")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, ValidationError)
        assert isinstance(error, InvalidDateError)


class TestInvalidDeadlineError:
    """Test InvalidDeadlineError exception"""

    def test_invalid_deadline_error_properties(self):
        """Test InvalidDeadlineError properties"""
        past_date = datetime(2020, 1, 1)
        error = InvalidDeadlineError(past_date)
        assert error.deadline_at == past_date
        assert str(error) == f"Deadline cannot be in the past: {past_date}"
        assert isinstance(error, ValidationError)

    def test_invalid_deadline_error_inheritance(self):
        """Test inheritance chain"""
        error = InvalidDeadlineError(datetime.now())
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, ValidationError)
        assert isinstance(error, InvalidDeadlineError)


class TestCallbackDataError:
    """Test CallbackDataError exception"""

    def test_callback_data_error_properties(self):
        """Test CallbackDataError properties"""
        error = CallbackDataError("invalid:data")
        assert error.callback_data == "invalid:data"
        assert str(error) == "Invalid callback data: invalid:data"
        assert isinstance(error, DeadlineBotError)

    def test_callback_data_error_inheritance(self):
        """Test inheritance chain"""
        error = CallbackDataError("bad_data")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, CallbackDataError)


class TestNotificationError:
    """Test NotificationError exception"""

    def test_notification_error_inheritance(self):
        """Test that NotificationError inherits from DeadlineBotError"""
        error = NotificationError("Notification failed")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, NotificationError)
        assert str(error) == "Notification failed"


class TestTimezoneConversionError:
    """Test TimezoneConversionError exception"""

    def test_timezone_conversion_error_properties(self):
        """Test TimezoneConversionError properties"""
        original_error = Exception("Original error")
        error = TimezoneConversionError("Europe/Invalid", original_error)
        assert error.timezone == "Europe/Invalid"
        assert error.original_error == original_error
        assert str(error) == "Failed to convert timezone: Europe/Invalid"
        assert isinstance(error, NotificationError)

    def test_timezone_conversion_error_no_original(self):
        """Test TimezoneConversionError without original error"""
        error = TimezoneConversionError("Invalid/Zone")
        assert error.timezone == "Invalid/Zone"
        assert error.original_error is None
        assert isinstance(error, NotificationError)

    def test_timezone_conversion_error_inheritance(self):
        """Test inheritance chain"""
        error = TimezoneConversionError("Mars/Phobos")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        assert isinstance(error, NotificationError)
        assert isinstance(error, TimezoneConversionError)


class TestDeadlineCreationError:
    """Test DeadlineCreationError exception"""

    def test_deadline_creation_error_inheritance(self):
        """Test that DeadlineCreationError inherits from ServiceError"""
        error = DeadlineCreationError("Failed to create deadline")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)
        # Note: ServiceError is not imported in exceptions.py,
        # so we test DeadlineBotError directly


class TestDeadlineUpdateError:
    """Test DeadlineUpdateError exception"""

    def test_deadline_update_error_inheritance(self):
        """Test that DeadlineUpdateError inherits from ServiceError"""
        error = DeadlineUpdateError("Failed to update deadline")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)


class TestDeadlineDeletionError:
    """Test DeadlineDeletionError exception"""

    def test_deadline_deletion_error_inheritance(self):
        """Test that DeadlineDeletionError inherits from ServiceError"""
        error = DeadlineDeletionError("Failed to delete deadline")
        assert isinstance(error, Exception)
        assert isinstance(error, DeadlineBotError)


class TestExceptionChaining:
    """Test exception chaining behavior"""

    def test_exception_with_cause(self):
        """Test exception with cause using 'from' syntax"""
        original_error = ValueError("Original error")

        try:
            raise InvalidTimezoneError("Invalid timezone") from original_error
        except InvalidTimezoneError as e:
            assert e.__cause__ == original_error
            assert isinstance(e, ValidationError)

    def test_exception_without_cause(self):
        """Test exception without cause"""
        error = InvalidDateError("bad date")
        assert error.__cause__ is None

    def test_exception_context(self):
        """Test exception context"""
        try:
            try:
                raise ValueError("Inner error")
            except ValueError:
                raise ValidationError("Outer error")
        except ValidationError as e:
            assert isinstance(e.__context__, ValueError)
            assert str(e.__context__) == "Inner error"


class TestExceptionEquality:
    """Test exception equality and identity"""

    def test_same_exceptions_equal(self):
        """Test that identical exceptions are equal"""
        error1 = DeadlineNotFoundError(123)
        error2 = DeadlineNotFoundError(123)
        assert error1.deadline_id == error2.deadline_id
        assert str(error1) == str(error2)
        assert error1 is not error2  # Different instances

    def test_different_exceptions_not_equal(self):
        """Test that different exceptions are not equal"""
        error1 = DeadlineNotFoundError(123)
        error2 = DeadlineNotFoundError(456)
        assert error1.deadline_id != error2.deadline_id
        assert str(error1) != str(error2)

    def test_different_exception_types_not_equal(self):
        """Test that different exception types are not equal"""
        error1 = DeadlineNotFoundError(123)
        error2 = InvalidTimezoneError("UTC")
        assert isinstance(error1, type(error2)) is False
        assert str(error1) != str(error2)


class TestExceptionAttributes:
    """Test exception custom attributes"""

    def test_all_exception_types_have_expected_attributes(self):
        """Test that all exception types have expected custom attributes"""

        # Test exceptions with custom attributes
        deadline_error = DeadlineNotFoundError(123)
        assert hasattr(deadline_error, "deadline_id")
        assert deadline_error.deadline_id == 123

        timezone_error = InvalidTimezoneError("UTC")
        assert hasattr(timezone_error, "timezone")
        assert timezone_error.timezone == "UTC"

        date_error = InvalidDateError("bad date")
        assert hasattr(date_error, "date_str")
        assert date_error.date_str == "bad date"

        deadline_time_error = InvalidDeadlineError(datetime.now())
        assert hasattr(deadline_time_error, "deadline_at")
        assert isinstance(deadline_time_error.deadline_at, datetime)

        callback_error = CallbackDataError("data")
        assert hasattr(callback_error, "callback_data")
        assert callback_error.callback_data == "data"

        tz_conv_error = TimezoneConversionError("Europe/Moscow")
        assert hasattr(tz_conv_error, "timezone")
        assert tz_conv_error.timezone == "Europe/Moscow"
        assert hasattr(tz_conv_error, "original_error")
