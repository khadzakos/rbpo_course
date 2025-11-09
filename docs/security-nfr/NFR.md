# NFR.md — Таблица требований безопасности

| ID     | Название | Описание | Метрика/Порог | Проверка (чем/где) | Компонент | Приоритет |
|--------|----------|----------|---------------|--------------------|-----------|-----------|
| NFR-01 | Аутентификация | Все API endpoints должны требовать аутентификации | JWT токен с TTL ≤ 15 минут | Unit тесты, security scan | API, Auth | High |
| NFR-02 | Защита от SQL-инъекций | Все SQL запросы должны использовать параметризованные запросы | 0% уязвимостей SQL-инъекций | SAST tools (Bandit), penetration testing | Database, ORM | Critical |
| NFR-03 | Валидация входных данных | Все входные данные должны валидироваться | 100% валидация через Pydantic | Unit тесты, API testing | API, Models | High |
| NFR-04 | Rate Limiting | Ограничение количества запросов | ≤ 100 запросов/минуту на IP | Load testing, monitoring | API Gateway | High |
| NFR-05 | Шифрование данных | Чувствительные данные должны быть зашифрованы | AES-256 для PII данных | Database audit | Database | Critical |
| NFR-06 | Безопасные заголовки HTTP | HTTP ответы должны содержать security headers | HSTS, CSP, X-Frame-Options | Security headers testing | Web Server | Medium |
| NFR-07 | Логирование безопасности | Security events должны логироваться | Логирование failed auth, suspicious activity | Security logs | Logging | High |
| NFR-08 | Защита от XSS | Пользовательские данные должны быть экранированы | 0% XSS уязвимостей | XSS testing, CSP | Frontend, API | High |
