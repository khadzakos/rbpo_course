# NFR_BDD.md — Приёмка в формате Gherkin

## NFR-01: Аутентификация

JWT Authentication
  Scenario: Valid JWT token allows API access
  - Given пользователь имеет валидный JWT токен
  - When пользователь делает запрос к защищенному endpoint
  - Then запрос должен быть обработан успешно
  - And время жизни токена должно быть ≤ 15 минут

  Scenario: Invalid JWT token is rejected
  - Given пользователь имеет невалидный JWT токен
  - When пользователь делает запрос к защищенному endpoint
  - Then запрос должен быть отклонен с кодом 401

## NFR-02: Защита от SQL-инъекций

SQL Injection Protection
  Scenario: Parameterized queries prevent SQL injection
  - Given система использует параметризованные запросы
  -When злоумышленник пытается внедрить SQL код
  - Then SQL код должен быть обработан как обычные данные
  - And база данных не должна быть скомпрометирована

## NFR-04: Rate Limiting

Rate Limiting Protection
  Scenario: Normal request rate is allowed
  - Given пользователь делает запросы в пределах лимита
  - When количество запросов ≤ 100 в минуту
  - Then все запросы должны обрабатываться успешно

  Scenario: Excessive request rate is blocked
  -Given пользователь превышает лимит запросов
  - When количество запросов > 100 в минуту
  - Then запросы должны блокироваться с кодом 429

## NFR-08: Защита от XSS

XSS Protection
  Scenario: Malicious scripts are sanitized
  - Given система получает данные с JavaScript кодом
  -When данные содержат потенциально опасный контент
  - Then скрипты должны быть экранированы
  - And в ответе не должно быть исполняемого кода
