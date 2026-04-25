# RoomFlow

RoomFlow - REST-сервис для управления репетиционными комнатами музыкальной студии. Проект помогает администратору вести каталог залов и оборудования, а клиентам - бронировать подходящее время без пересечений.

## Предметная область

В студии есть несколько комнат с разной вместимостью, ценой и набором оборудования. Пользователь выбирает время, число участников и нужную технику. Сервис проверяет доступность комнаты, считает стоимость бронирования и предлагает лучшие свободные слоты.

## Что реализовано

- JWT/OAuth2-аутентификация: регистрация, вход, профиль текущего пользователя.
- Роли `admin` и `member`: первый зарегистрированный пользователь становится администратором.
- Реляционная SQLite-БД с автоматическим созданием файла при запуске.
- Связанные таблицы: `users`, `rooms`, `equipment`, `room_equipment`, `bookings`.
- CRUD для пользователей, комнат, оборудования и бронирований.
- Бизнес-алгоритм подбора комнаты по вместимости, оборудованию, бюджету, времени и занятости.
- Валидация входных данных через Pydantic.
- Единый формат ошибок.
- Автоматические тесты на `TestClient` с покрытием выше 70%.
- Страница `/` с понятной навигацией к Swagger и ReDoc.

## Основные эндпоинты

| Метод | Путь | Назначение |
| --- | --- | --- |
| POST | `/api/v1/auth/register` | Регистрация |
| POST | `/api/v1/auth/login` | Получение JWT |
| GET | `/api/v1/auth/me` | Профиль текущего пользователя |
| GET | `/api/v1/users` | Список пользователей |
| GET | `/api/v1/users/{user_id}` | Пользователь по id |
| PATCH | `/api/v1/users/{user_id}` | Обновление пользователя |
| DELETE | `/api/v1/users/{user_id}` | Удаление пользователя |
| GET | `/api/v1/equipment` | Список оборудования |
| POST | `/api/v1/equipment` | Создание оборудования |
| GET | `/api/v1/equipment/{equipment_id}` | Оборудование по id |
| PATCH | `/api/v1/equipment/{equipment_id}` | Обновление оборудования |
| DELETE | `/api/v1/equipment/{equipment_id}` | Удаление оборудования |
| GET | `/api/v1/rooms` | Список комнат |
| POST | `/api/v1/rooms` | Создание комнаты |
| GET | `/api/v1/rooms/{room_id}` | Комната по id |
| PATCH | `/api/v1/rooms/{room_id}` | Обновление комнаты |
| DELETE | `/api/v1/rooms/{room_id}` | Удаление комнаты |
| GET | `/api/v1/bookings` | Список бронирований |
| POST | `/api/v1/bookings` | Создание бронирования |
| GET | `/api/v1/bookings/{booking_id}` | Бронирование по id |
| PATCH | `/api/v1/bookings/{booking_id}` | Обновление бронирования |
| DELETE | `/api/v1/bookings/{booking_id}` | Удаление бронирования |
| POST | `/api/v1/recommendations/rooms` | Подбор лучших свободных слотов |
| GET | `/api/v1/system/health` | Проверка сервиса |

## Бизнес-алгоритм

Эндпоинт `POST /api/v1/recommendations/rooms` принимает число участников, список нужного оборудования, временное окно, длительность и максимальный бюджет. Сервис проходит по комнатам и 30-минутным слотам, исключает занятые интервалы, проверяет вместимость и оборудование, затем ранжирует варианты по цене, запасу вместимости и близости времени.

Пример запроса:

```json
{
  "participants": 4,
  "equipment_ids": [1, 2],
  "starts_after": "2026-05-01T10:00:00",
  "ends_before": "2026-05-01T16:00:00",
  "duration_minutes": 120,
  "max_price": 4000,
  "limit": 3
}
```

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ROOMFLOW_SECRET_KEY="local-dev-secret-change-me"
uvicorn app.main:app --reload
```

После запуска:

- стартовая страница: `http://127.0.0.1:8000/`
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

Если `ROOMFLOW_DATABASE_URL` не задан, используется `sqlite:///./roomflow.db`.

## Docker

```bash
export ROOMFLOW_SECRET_KEY="local-dev-secret-change-me"
docker compose up --build
```

Сервис будет доступен на `http://127.0.0.1:8000`.

## Демонстрационные данные

```bash
export ROOMFLOW_SECRET_KEY="local-dev-secret-change-me"
export ROOMFLOW_ADMIN_EMAIL="admin@example.com"
export ROOMFLOW_ADMIN_PASSWORD="StrongPass123"
python scripts/seed_demo.py
```

После этого можно войти через Swagger, используя email и пароль из переменных окружения.

## Тесты

```bash
pytest --cov=app --cov-report=term-missing
```

Последний прогон:

```text
11 passed
TOTAL 90%
```

## Pylint

```bash
pylint app > pylint.txt
```

Файл `pylint.txt` лежит в корне проекта.

## Структура

```text
app/
  main.py
  models.py
  schemas.py
  routers/
  services/
tests/
scripts/
docs/
```

## Автор

Александра Шумрикова
