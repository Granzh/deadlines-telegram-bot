from collections import defaultdict

"""User-friendly error messages for the Telegram bot"""

# Error messages in Russian
ERROR_MESSAGES = {
    # General errors
    "general_error": "Произошла ошибка. Попробуйте позже.",
    "validation_error": "Ошибка валидации данных. Проверьте введенные значения.",
    "database_error": "Ошибка базы данных. Попробуйте позже.",
    # Deadline errors
    "deadline_not_found": "Дедлайн не найден.",
    "deadline_create_error": """Не удалось создать дедлайн.
    Проверьте данные и попробуйте снова.""",
    "deadline_update_error": "Не удалось обновить дедлайн. Попробуйте позже.",
    "deadline_delete_error": "Не удалось удалить дедлайн. Попробуйте позже.",
    "deadline_in_past": "Дедлайн не может быть в прошлом.",
    "deadline_empty_title": "Название дедлайна не может быть пустым.",
    # Timezone errors
    "invalid_timezone": "Неверный часовой пояс. Используйте формат 'Europe/Moscow'.",
    "timezone_conversion_error": "Ошибка преобразования часового пояса.",
    # Date parsing errors
    "invalid_date": """Не удалось распознать дату.
    Используйте формат 'ДД.ММ.ГГГГ ЧЧ:ММ'.""",
    "date_in_past": "Дата не может быть в прошлом.",
    # Callback data errors
    "invalid_callback_data": "Некорректные данные. Попробуйте снова.",
    "invalid_deadline_id": "Неверный ID дедлайна.",
    # Notification errors
    "notification_error": "Ошибка отправки уведомления.",
    "notification_settings_error": "Ошибка настроек уведомлений.",
    # Input validation
    "empty_input": "Поле не может быть пустым.",
    "too_long_input": """Слишком длинный текст. Максимальная длина: {max_length} символов.
    Попробуйте сократить текст.""",
    "invalid_number": "Неверный формат числа.",
    # Rate limiting
    "rate_limit": "Слишком много запросов. Подождите немного перед следующей командой.",
    # Unknown commands
    "unknown_command": "Неизвестная команда. Используйте /help для списка доступных команд.",
    "unknown_message": "Я не понимаю это сообщение. Используйте /help для справки.",
    # File/operation errors
    "file_not_found": "Файл не найден.",
    "permission_denied": "Недостаточно прав для выполнения операции.",
    # Network errors
    "network_error": "Ошибка сети. Проверьте подключение к интернету.",
    "timeout_error": "Превышено время ожидания. Попробуйте позже.",
}

# Success messages
SUCCESS_MESSAGES = {
    "deadline_created": "✅ Дедлайн успешно создан!",
    "deadline_updated": "✅ Дедлайн успешно обновлен!",
    "deadline_deleted": "✅ Дедлайн удален!",
    "timezone_updated": "✅ Часовой пояс обновлен!",
    "notifications_enabled": "✅ Уведомления включены!",
    "notifications_disabled": "✅ Уведомления отключены!",
    "settings_saved": "✅ Настройки сохранены!",
}

# Help messages
HELP_MESSAGES = {
    "no_deadlines": "У вас нет дедлайнов.",
    "no_deadlines_to_edit": "У вас нет дедлайнов для редактирования.",
    "choose_deadline": "Выберите дедлайн:",
    "enter_title": "Введите название дедлайна:",
    "enter_date": "Введите дату и время дедлайна (ДД.ММ.ГГГГ ЧЧ:ММ):",
    "enter_timezone": "Введите часовой пояс (например, Europe/Moscow):",
    "deadline_saved": "Дедлайн сохранен!",
    "title_too_long": "Название слишком длинное (макс. 200 символов).",
}

# Validation messages
VALIDATION_MESSAGES = {
    "title_required": "Название дедлайна обязательно.",
    "title_too_long": "Название слишком длинное (макс. 200 символов).",
    "date_required": "Дата обязательна.",
    "date_invalid": "Неверный формат даты. Используйте ДД.ММ.ГГГГ ЧЧ:ММ.",
    "date_past": "Дата не может быть в прошлом.",
    "timezone_required": "Часовой пояс обязателен.",
    "timezone_invalid": "Неверный часовой пояс. Пример: Europe/Moscow.",
}


def get_error_message(error_type: str, **kwargs) -> str:
    """Get error message by type with optional formatting"""
    message = ERROR_MESSAGES.get(error_type, ERROR_MESSAGES["general_error"])
    safe_kwargs = defaultdict(str, kwargs)
    return message.format_map(safe_kwargs)


def get_success_message(success_type: str, **kwargs) -> str:
    """Get success message by type with optional formatting"""
    message = SUCCESS_MESSAGES.get(success_type, "Операция выполнена успешно!")
    return message.format(**kwargs)


def get_help_message(help_type: str, **kwargs) -> str:
    """Get help message by type with optional formatting"""
    message = HELP_MESSAGES.get(help_type, "")
    safe_kwargs = defaultdict(str, kwargs)
    return message.format_map(safe_kwargs)


def get_validation_message(validation_type: str, **kwargs) -> str:
    """Get validation message by type with optional formatting"""
    message = VALIDATION_MESSAGES.get(validation_type, "Ошибка валидации.")
    return message.format(**kwargs)


# Custom error message formatters for specific exceptions
def format_deadline_error(error) -> str:
    """Format deadline-related errors"""
    if hasattr(error, "deadline_at"):
        return get_error_message("deadline_in_past", deadline=error.deadline_at)
    return get_error_message("deadline_create_error")


def format_validation_error(error) -> str:
    """Format validation errors"""
    message = str(error)
    if "empty" in message.lower():
        return get_error_message("empty_input")
    elif "long" in message.lower():
        return get_error_message("too_long_input", max_length=200)
    elif "date" in message.lower():
        return get_error_message("invalid_date")
    elif "timezone" in message.lower():
        return get_error_message("invalid_timezone")
    return get_error_message("validation_error", details=message)


def format_callback_error(error) -> str:
    """Format callback data errors"""
    if hasattr(error, "callback_data"):
        return get_error_message("invalid_callback_data", data=error.callback_data)
    return get_error_message("invalid_callback_data")


# Mapping of exception types to message formatters
EXCEPTION_FORMATTERS = {
    "InvalidDeadlineError": format_deadline_error,
    "ValidationError": format_validation_error,
    "CallbackDataError": format_callback_error,
    "InvalidTimezoneError": lambda e: get_error_message("invalid_timezone"),
    "InvalidDateError": lambda e: get_error_message("invalid_date"),
    "DeadlineNotFoundError": lambda e: get_error_message("deadline_not_found"),
    "DatabaseError": lambda e: get_error_message("database_error"),
    "NotificationError": lambda e: get_error_message("notification_error"),
}


def format_exception_message(error: Exception) -> str:
    """Format exception into user-friendly message"""
    error_type = type(error).__name__
    formatter = EXCEPTION_FORMATTERS.get(error_type)

    if formatter:
        return formatter(error)

    # Fallback to general error
    logger = __import__("logging").getLogger(__name__)
    logger.warning(f"No formatter for exception type: {error_type}")
    return get_error_message("general_error")
