class DeadlineBotError(Exception):
    """Base exception for deadline bot application"""

    pass


class DatabaseError(DeadlineBotError):
    """Database related errors"""

    pass


class DeadlineNotFoundError(DatabaseError):
    """Raised when deadline is not found"""

    def __init__(self, deadline_id: int):
        self.deadline_id = deadline_id
        super().__init__(f"Deadline with id {deadline_id} not found")


class ValidationError(DeadlineBotError):
    """Validation errors for user input"""

    pass


class InvalidTimezoneError(ValidationError):
    """Raised when timezone is invalid"""

    def __init__(self, timezone: str):
        self.timezone = timezone
        super().__init__(f"Invalid timezone: {timezone}")


class InvalidDateError(ValidationError):
    """Raised when date cannot be parsed"""

    def __init__(self, date_str: str):
        self.date_str = date_str
        super().__init__(f"Cannot parse date: {date_str}")


class InvalidDeadlineError(ValidationError):
    """Raised when deadline is in the past"""

    def __init__(self, deadline_at):
        self.deadline_at = deadline_at
        super().__init__(f"Deadline cannot be in the past: {deadline_at}")


class CallbackDataError(DeadlineBotError):
    """Errors in callback data parsing"""

    def __init__(self, callback_data: str):
        self.callback_data = callback_data
        super().__init__(f"Invalid callback data: {callback_data}")


class NotificationError(DeadlineBotError):
    """Notification related errors"""

    pass


class TimezoneConversionError(NotificationError):
    """Error in timezone conversion"""

    def __init__(self, timezone: str, original_error: Exception | None = None):
        self.timezone = timezone
        self.original_error = original_error
        super().__init__(f"Failed to convert timezone: {timezone}")


class ServiceError(DeadlineBotError):
    """Service layer errors"""

    pass


class DeadlineCreationError(ServiceError):
    """Error creating deadline"""

    pass


class DeadlineUpdateError(ServiceError):
    """Error updating deadline"""

    pass


class DeadlineDeletionError(ServiceError):
    """Error deleting deadline"""

    pass
