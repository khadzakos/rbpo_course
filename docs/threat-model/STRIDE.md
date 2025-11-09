# STRIDE — Угрозы и контроли для Chore Tracker API

| Поток/Элемент | Угроза (S/T/R/I/D/E) | Описание угрозы | Контроль | Ссылка на NFR | Проверка/Артефакт |
|---------------|-----------------------|------------------|----------|---------------|-------------------|
| F1 (Client → API) | S | Spoofing: Подделка клиентских запросов, маскировка под легитимного пользователя | JWT токены с подписью, валидация токенов | NFR-01 | Unit тесты аутентификации, security scan |
| F1 (Client → API) | T | Tampering: Модификация HTTP запросов, подмена данных | HTTPS, валидация входных данных через Pydantic | NFR-03 | API testing, input validation tests |
| F1 (Client → API) | I | Information Disclosure: Утечка чувствительных данных в ответах | Фильтрация ответов, исключение PII из логов | NFR-05 | Data leak testing, response analysis |
| F1 (Client → API) | D | Denial of Service: Перегрузка API запросами | Rate limiting, throttling | NFR-04 | Load testing, monitoring |
| F1 (Client → API) | E | Elevation of Privilege: Получение несанкционированного доступа | Роли и права доступа, авторизация | NFR-01 | Authorization testing, RBAC audit |
| F8 (Repositories → Database) | S | Spoofing: Подделка SQL запросов, маскировка под ORM | Параметризованные запросы SQLAlchemy | NFR-02 | SAST tools (Bandit), SQL injection testing |
| F8 (Repositories → Database) | T | Tampering: Модификация данных в БД | Транзакции, валидация на уровне БД | NFR-02 | Database integrity checks, transaction testing |
| F8 (Repositories → Database) | I | Information Disclosure: Утечка данных из БД | Шифрование БД, контроль доступа | NFR-05 | Database encryption audit, access control |
| F8 (Repositories → Database) | D | Denial of Service: Перегрузка БД запросами | Connection pooling, query optimization | NFR-04 | Database performance testing, monitoring |
| F8 (Repositories → Database) | E | Elevation of Privilege: Несанкционированный доступ к БД | Минимальные права БД, принцип least privilege | NFR-01 | Database permissions audit, RBAC |
| API Gateway | T | Tampering: Модификация API конфигурации | Конфигурация в коде, версионирование | NFR-06 | Configuration audit, version control |
| API Gateway | I | Information Disclosure: Утечка API метаданных | Скрытие версий, ограничение информации | NFR-06 | Security headers testing, metadata audit |
| UserService | T | Tampering: Модификация пользовательских профилей | Валидация входных данных, санитизация | NFR-03 | Input sanitization testing, profile validation |
| UserService | I | Information Disclosure: Утечка пользовательских данных | Контроль доступа к профилям | NFR-05 | User data access testing, privacy audit |
| Database | I | Information Disclosure: Утечка данных из БД | Шифрование на уровне БД, backup шифрование | NFR-05 | Database encryption audit, backup security |

## Обоснования исключений

### Не применимые угрозы:
- **XSS атаки**: Приложение не имеет frontend компонентов, только API
- **CSRF атаки**: API использует stateless архитектуру с JWT токенами
- **Session hijacking**: Нет сессий, используется JWT
- **File upload атаки**: Нет функционала загрузки файлов
- **Directory traversal**: Нет файловой системы доступа
