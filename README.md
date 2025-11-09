# Chore Tracker

Трекер дел между участниками - API для управления пользователями, задачами и назначениями.

## Архитектура

- **User** - пользователи системы
- **Chore** - задачи с периодичностью (title, cadence)
- **Assignment** - назначения задач пользователям (user_id, due_at, status)

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
pre-commit install
python app/main.py
# или
uvicorn app.main:app --reload
```

## Ритуал перед PR
```bash
ruff check --fix .
black .
isort .
pytest -q
pre-commit run --all-files
```

## Тесты
```bash
pytest -q
```

## Контейнеры
```bash
docker build -t chore-tracker .
docker run --rm -p 8000:8000 chore-tracker
# или
docker-compose up --build
```

## API Endpoints

### Пользователи
- `GET /users` - получить всех пользователей
- `GET /users/{user_id}` - получить пользователя по ID
- `POST /users` - создать пользователя
- `PUT /users/{user_id}` - обновить пользователя
- `DELETE /users/{user_id}` - удалить пользователя

### Задачи
- `GET /chores` - получить все задачи
- `GET /chores/{chore_id}` - получить задачу по ID
- `POST /chores` - создать задачу
- `PUT /chores/{chore_id}` - обновить задачу
- `DELETE /chores/{chore_id}` - удалить задачу

### Назначения
- `GET /assignments` - получить все назначения
- `GET /assignments/{assignment_id}` - получить назначение по ID
- `POST /assignments` - создать назначение
- `PUT /assignments/{assignment_id}` - обновить статус назначения
- `DELETE /assignments/{assignment_id}` - удалить назначение

### Статистика
- `GET /statistics` - получить статистику по назначениям

### Health Check
- `GET /health` → `{"status": "ok"}`

## Модели данных

### User
```json
{
  "id": 1,
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2024-01-01T00:00:00"
}
```

### Chore
```json
{
  "id": 1,
  "title": "Помыть посуду",
  "cadence": "daily",
  "created_at": "2024-01-01T00:00:00"
}
```

### Assignment
```json
{
  "id": 1,
  "user_id": 1,
  "chore_id": 1,
  "due_at": "2024-01-02T18:00:00",
  "status": "pending",
  "created_at": "2024-01-01T00:00:00",
  "completed_at": null
}
```

## Статусы назначений
- `pending` - ожидает выполнения
- `in_progress` - в процессе
- `completed` - завершено
- `overdue` - просрочено

## Периодичность задач
- `daily` - ежедневно
- `weekly` - еженедельно
- `monthly` - ежемесячно
- `yearly` - ежегодно

## База данных
По умолчанию используется SQLite (`./chore_tracker.db`).
Для изменения базы данных установите переменную окружения `DATABASE_URL`.

## Swagger документация
После запуска приложения документация доступна по адресам:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Формат ошибок
Все ошибки возвращаются в JSON формате:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid cadence. Must be one of: ['daily', 'weekly', 'monthly', 'yearly']"
  }
}
```

## CI
В репозитории настроен workflow **CI** (GitHub Actions) — required check для `main`.
Badge добавится автоматически после загрузки шаблона в GitHub.

См. также: `SECURITY.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`.
