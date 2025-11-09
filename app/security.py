import logging
import os
import re
import uuid
from datetime import datetime
from typing import Optional


class SecureHTTPException(Exception):
    """Безопасное исключение HTTP с поддержкой RFC 7807"""

    def __init__(
        self,
        error_type: str,
        title: str,
        detail: str,
        status_code: int,
        correlation_id: Optional[str] = None,
        instance: Optional[str] = None,
    ):
        self.error_type = error_type
        self.title = title
        self.detail = detail
        self.status_code = status_code
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.instance = instance
        super().__init__(detail)


class ErrorResponse:
    """Стандартизированный ответ об ошибке RFC 7807"""

    def __init__(
        self,
        type: str,
        title: str,
        status: int,
        detail: str,
        instance: str,
        correlation_id: str,
    ):
        self.type = type
        self.title = title
        self.status = status
        self.detail = detail
        self.instance = instance
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow().isoformat()

    def dict(self):
        return {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
        }


class InputValidator:
    """Валидатор входных данных с защитой от атак"""

    # Разрешенные MIME типы для загрузки файлов
    ALLOWED_MIME_TYPES = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
        "text/plain",
    ]

    # Максимальный размер файла (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # Максимальное время загрузки (30 секунд)
    MAX_UPLOAD_TIME = 30

    # Опасные символы для path traversal
    DANGEROUS_CHARS = ["..", "/", "\\", "~", "$", "`"]

    @staticmethod
    def validate_email(email: str) -> bool:
        """Валидация email адреса"""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_filename(filename: str) -> str:
        """Валидация и санитизация имени файла"""
        # Удаление опасных символов
        for char in InputValidator.DANGEROUS_CHARS:
            filename = filename.replace(char, "")

        # Генерация UUID имени для безопасности
        name, ext = os.path.splitext(filename)
        safe_name = f"{uuid.uuid4()}{ext}"

        return safe_name

    @staticmethod
    def validate_file_size(size: int) -> bool:
        """Проверка размера файла"""
        return size <= InputValidator.MAX_FILE_SIZE

    @staticmethod
    def validate_mime_type(mime_type: str) -> bool:
        """Проверка MIME типа файла"""
        return mime_type in InputValidator.ALLOWED_MIME_TYPES

    @staticmethod
    def sanitize_string(value: str, max_length: int = 255) -> str:
        """Санитизация строки"""
        clean = re.sub(r"<[^>]*>.*?</[^>]*>", "", value, flags=re.DOTALL)
        clean = re.sub(r"<[^>]+>", "", clean)
        dangerous_patterns = [
            r"javascript:",
            r"alert\s*\(",
            r"eval\s*\(",
            r"exec\s*\(",
            r"document\.",
            r"window\.",
            r"on\w+\s*=",
        ]
        for pattern in dangerous_patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)

        # Удаление SQL и HTML инъекций
        sql_patterns = [
            r"DROP\s+TABLE",
            r"DELETE\s+FROM",
            r"INSERT\s+INTO",
            r"UPDATE\s+SET",
            r"SELECT\s+.*\s+FROM",
            r"UNION\s+SELECT",
            r"OR\s+1\s*=\s*1",
            r"AND\s+1\s*=\s*1",
            r";\s*--",
            r"/\*.*?\*/",
        ]
        for pattern in sql_patterns:
            clean = re.sub(pattern, "", clean, flags=re.IGNORECASE)
        # Ограничение длины
        clean = clean[:max_length]
        # Удаление опасных символов
        for char in ["<", ">", '"', "'", "&"]:
            clean = clean.replace(char, "")
        return clean.strip()

    @staticmethod
    def validate_path(path: str) -> str:
        """Канонизация и валидация пути"""
        # Канонизация пути
        canonical_path = os.path.normpath(path)
        # Проверка на path traversal
        if ".." in canonical_path or canonical_path.startswith("/"):
            raise ValueError("Invalid path: potential path traversal detected")
        return canonical_path


class SecretMaskingFilter(logging.Filter):
    """Фильтр для маскирования секретов в логах"""

    SECRET_PATTERNS = [
        "password",
        "token",
        "key",
        "secret",
        "auth",
        "credential",
        "api_key",
        "access_token",
    ]

    def filter(self, record):
        message = record.getMessage()
        for pattern in self.SECRET_PATTERNS:
            if pattern.lower() in message.lower():
                record.msg = re.sub(
                    rf"({pattern}[=:]\s*)([^\s,]+)",
                    r"\1***MASKED***",
                    record.msg,
                    flags=re.IGNORECASE,
                )
        return True


class SecretsManager:
    """Менеджер секретов с поддержкой ротации"""

    def __init__(self):
        self.vault_url = os.getenv("VAULT_URL")
        self.vault_token = os.getenv("VAULT_TOKEN")
        self.fallback_to_env = os.getenv("FALLBACK_TO_ENV", "true").lower() == "true"

    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Получение секрета с fallback на переменные окружения"""
        try:
            # В продакшене здесь будет интеграция с Vault
            if self.vault_url and self.vault_token:
                # TODO: Implement Vault integration
                pass

            # Fallback на переменные окружения
            if self.fallback_to_env:
                return os.getenv(key.upper(), default)

            return default
        except Exception as e:
            logging.error(f"Failed to retrieve secret {key}: {e}")
            return default

    def mask_secret_in_logs(self, value: str) -> str:
        """Маскирование секрета для логов"""
        if len(value) <= 4:
            return "***"
        return f"{value[:2]}***{value[-2:]}"


def create_error_response(
    request,
    error_type: str,
    title: str,
    detail: str,
    status_code: int,
    correlation_id: Optional[str] = None,
):
    """Создание стандартизированного ответа об ошибке RFC 7807"""

    correlation_id = correlation_id or str(uuid.uuid4())

    error_response = ErrorResponse(
        type=error_type,
        title=title,
        status=status_code,
        detail=detail,
        instance=str(request.url) if hasattr(request, "url") else "/api",
        correlation_id=correlation_id,
    )

    return {
        "status_code": status_code,
        "content": error_response.dict(),
        "headers": {"X-Correlation-ID": correlation_id},
    }


def setup_security_logging():
    """Настройка безопасного логирования"""
    # Добавление фильтра маскирования секретов
    for handler in logging.root.handlers:
        handler.addFilter(SecretMaskingFilter())

    # Настройка уровня логирования для безопасности
    logging.getLogger("security").setLevel(logging.INFO)


# Предопределенные типы ошибок
ERROR_TYPES = {
    "validation_error": "https://api.choretracker.com/errors/validation-error",
    "authentication_error": "https://api.choretracker.com/errors/authentication-error",
    "authorization_error": "https://api.choretracker.com/errors/authorization-error",
    "not_found_error": "https://api.choretracker.com/errors/not-found-error",
    "internal_error": "https://api.choretracker.com/errors/internal-error",
}
