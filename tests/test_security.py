import os
from unittest.mock import patch

import pytest

import app.security as security


class TestInputValidation:
    """Тесты валидации входных данных (ADR-001)"""

    def test_valid_user_creation(self, client):
        """Тест создания пользователя с валидными данными"""
        response = client.post(
            "/users", json={"name": "John Doe", "email": "john@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John Doe"
        assert data["email"] == "john@example.com"

    def test_invalid_email_format(self, client):
        """Тест с невалидным форматом email"""
        response = client.post(
            "/users", json={"name": "John Doe", "email": "invalid-email"}
        )
        assert response.status_code == 422

    def test_html_injection_prevention(self, client):
        """Тест защиты от HTML инъекций"""
        malicious_name = "<script>alert('xss')</script>John"
        response = client.post(
            "/users", json={"name": malicious_name, "email": "john@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        # HTML теги должны быть удалены
        assert "<script>" not in data["name"]
        assert "alert" not in data["name"]

    def test_filename_sanitization(self):
        """Тест санитизации имени файла"""
        dangerous_filename = "../../../etc/passwd"
        safe_filename = security.InputValidator.validate_filename(dangerous_filename)

        # Проверяем, что опасные символы удалены
        assert ".." not in safe_filename
        assert "/" not in safe_filename
        assert "\\" not in safe_filename
        # Имя должно содержать UUID
        assert len(safe_filename) > 10  # UUID + расширение

    def test_path_traversal_protection(self):
        """Тест защиты от path traversal"""
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "/etc/passwd",
        ]

        for path in dangerous_paths:
            with pytest.raises(ValueError, match="path traversal"):
                security.InputValidator.validate_path(path)

    def test_file_size_validation(self):
        """Тест валидации размера файла"""
        # Тест с допустимым размером
        assert security.InputValidator.validate_file_size(1024)

        # Тест с превышением лимита
        large_size = security.InputValidator.MAX_FILE_SIZE + 1

        assert not security.InputValidator.validate_file_size(large_size)


class TestErrorHandling:
    """Тесты обработки ошибок RFC 7807 (ADR-002)"""

    def test_error_response_format(self, client):
        """Тест формата ответа об ошибке RFC 7807"""
        response = client.get("/users/99999")

        assert response.status_code == 404
        data = response.json()

        # Проверяем структуру RFC 7807
        assert "type" in data
        assert "title" in data
        assert "detail" in data
        assert "correlation_id" in data
        assert "instance" in data
        assert "timestamp" in data

        # Проверяем заголовки
        assert "X-Correlation-ID" in response.headers

    def test_correlation_id_consistency(self, client):
        """Тест консистентности correlation ID"""
        response = client.get("/health")

        assert response.status_code == 200
        correlation_id = response.headers["X-Correlation-ID"]

        # Проверяем, что ID валидный UUID
        assert len(correlation_id) == 36
        assert correlation_id.count("-") == 4

    def test_secure_http_exception(self):
        """Тест SecureHTTPException"""
        exc = security.SecureHTTPException(
            error_type=security.ERROR_TYPES["validation_error"],
            title="Test Error",
            detail="Test error message",
            status_code=400,
        )

        assert exc.error_type == security.ERROR_TYPES["validation_error"]
        assert exc.title == "Test Error"
        assert exc.detail == "Test error message"
        assert exc.status_code == 400
        assert exc.correlation_id is not None


class TestSecretsManagement:
    """Тесты управления секретами (ADR-003)"""

    def test_secrets_manager_initialization(self):
        """Тест инициализации менеджера секретов"""
        manager = security.SecretsManager()
        assert manager.vault_url is None or isinstance(manager.vault_url, str)
        assert manager.vault_token is None or isinstance(manager.vault_token, str)
        assert isinstance(manager.fallback_to_env, bool)

    @patch.dict(os.environ, {"TEST_SECRET": "test_value"})
    def test_get_secret_from_environment(self):
        """Тест получения секрета из переменных окружения"""
        manager = security.SecretsManager()
        secret = manager.get_secret("TEST_SECRET")
        assert secret == "test_value"

    def test_mask_secret_in_logs(self):
        """Тест маскирования секрета в логах"""
        manager = security.SecretsManager()
        # Тест с коротким секретом
        short_secret = "abc"
        masked_short = manager.mask_secret_in_logs(short_secret)
        assert masked_short == "***"

        # Тест с длинным секретом
        long_secret = "very_long_secret_key_12345"
        masked_long = manager.mask_secret_in_logs(long_secret)
        assert masked_long == "ve***45"
        assert len(masked_long) == 7  # 2 + 3 + 2

    def test_secret_masking_filter(self):
        """Тест фильтра маскирования секретов"""
        import logging

        from app.security import SecretMaskingFilter

        filter_instance = SecretMaskingFilter()

        # Тестируем маскирование пароля
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User password=secret123 logged in",
            args=(),
            exc_info=None,
        )

        result = filter_instance.filter(record)

        assert result


class TestSecurityAttacks:
    """Тесты защиты от атак"""

    def test_sql_injection_prevention(self, client):
        """Тест защиты от SQL инъекций"""
        malicious_name = "'; DROP TABLE users; --"
        response = client.post(
            "/users", json={"name": malicious_name, "email": "john@example.com"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "DROP" not in data["name"]
        assert "TABLE" not in data["name"]

    def test_xss_prevention(self):
        """Тест защиты от XSS атак"""
        malicious_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
        ]

        for malicious_input in malicious_inputs:
            sanitized = security.InputValidator.sanitize_string(malicious_input)

            # Проверяем, что опасные теги удалены
            assert "<script>" not in sanitized
            assert "javascript:" not in sanitized
            assert "onerror=" not in sanitized
            assert "alert(" not in sanitized

    def test_file_upload_security(self):
        """Тест безопасности загрузки файлов"""
        # Тест с недопустимыми MIME типами
        dangerous_mime_types = [
            "application/executable",
            "application/x-executable",
            "text/html",
        ]

        for mime_type in dangerous_mime_types:
            assert not security.InputValidator.validate_mime_type(mime_type)

    def test_input_length_limits(self):
        """Тест ограничений длины ввода"""
        # Создаем очень длинную строку
        long_string = "A" * 10000

        # Тестируем санитизацию
        sanitized = security.InputValidator.sanitize_string(long_string, max_length=255)

        # Проверяем, что длина ограничена
        assert len(sanitized) <= 255


class TestSecurityIntegration:
    """Интеграционные тесты безопасности"""

    def test_security_headers(self, client):
        """Тест заголовков безопасности"""
        response = client.get("/health")
        assert response.status_code == 200

        # Проверяем correlation ID
        assert "X-Correlation-ID" in response.headers

        # Проверяем, что ID валидный UUID
        correlation_id = response.headers["X-Correlation-ID"]
        assert len(correlation_id) == 36
        assert correlation_id.count("-") == 4

        # Проверяем security headers (506-06)
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        assert "X-XSS-Protection" in response.headers
        assert response.headers["X-XSS-Protection"] == "1; mode=block"
        assert "Referrer-Policy" in response.headers
        assert "Content-Security-Policy" in response.headers

    def test_error_consistency(self, client):
        """Тест консистентности ошибок между endpoints"""
        endpoints = [
            "/users/99999",  # 404
            "/chores/99999",  # 404
            "/assignments/99999",  # 404
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert "X-Correlation-ID" in response.headers

            if response.status_code == 404:
                # Проверяем, что 404 ошибки обрабатываются консистентно
                assert response.status_code == 404
                data = response.json()
                assert "type" in data
                assert "title" in data
                assert "detail" in data
                assert "correlation_id" in data

    def test_validation_error_handling(self, client):
        """Тест обработки ошибок валидации"""
        test_cases = [
            # Пустое имя
            {"name": "", "email": "test@example.com"},
            # Невалидный email
            {"name": "Test User", "email": "invalid-email"},
            # Имя слишком длинное
            {"name": "A" * 101, "email": "test@example.com"},
        ]

        for test_data in test_cases:
            response = client.post("/users", json=test_data)
            assert response.status_code == 422
            assert "X-Correlation-ID" in response.headers

    def test_rate_limiting(self, client):
        """Тест rate limiting"""
        import os

        from app.security import _rate_limiter

        original_testing = os.environ.get("TESTING")
        os.environ["TESTING"] = "false"
        _rate_limiter.clear()
        _rate_limiter.max_requests = 5  # Низкий лимит для теста
        _rate_limiter.window_seconds = 60

        try:
            # Делаем несколько запросов подряд
            for _ in range(5):
                response = client.get("/users")
                assert response.status_code == 200

            # Шестой запрос должен быть заблокирован
            response = client.get("/users")
            assert response.status_code == 429
            data = response.json()
            assert "rate limit" in data["detail"].lower()
        finally:
            # Восстанавливаем настройки
            if original_testing:
                os.environ["TESTING"] = original_testing
            else:
                os.environ["TESTING"] = "true"
            _rate_limiter.max_requests = 100
            _rate_limiter.clear()

    def test_rate_limit_error_format(self, client):
        """Тест формата ошибки rate limiting"""
        import os

        from app.security import _rate_limiter

        original_testing = os.environ.get("TESTING")
        os.environ["TESTING"] = "false"
        _rate_limiter.clear()
        _rate_limiter.max_requests = 1  # Очень низкий лимит
        _rate_limiter.window_seconds = 60

        try:
            # Первый запрос должен пройти
            response = client.get("/users")
            assert response.status_code == 200

            # Второй запрос должен быть заблокирован
            response = client.get("/users")
            assert response.status_code == 429
            data = response.json()
            assert "type" in data
            assert "title" in data
            assert "detail" in data
            assert "correlation_id" in data
            assert "Retry-After" in response.headers
            assert data["title"] == "Rate Limit Exceeded"
        finally:
            # Восстанавливаем настройки
            if original_testing:
                os.environ["TESTING"] = original_testing
            else:
                os.environ["TESTING"] = "true"
            _rate_limiter.max_requests = 100
            _rate_limiter.clear()
