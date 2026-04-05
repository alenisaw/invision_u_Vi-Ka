# API

## Обзор

Базовый URL backend:

`http://localhost:8000`

Базовый URL frontend proxy:

`http://localhost:3000/api/backend/*`

Next.js proxy переписывает `/api/backend/*` в backend `/api/v1/*`.

Модель аутентификации:

- вход создает HTTP-only session cookie
- защищенные маршруты используют session auth на backend
- доступ ограничивается через RBAC

В публичной документации используются названия этапов:

- `Input Intake`
- `ASR`
- `Privacy`
- `Profile`
- `Extraction`
- `AI Detect`
- `Scoring`
- `Explanation`
- `Review`

## Response envelope

Успешный ответ:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "meta": {
    "timestamp": "2026-03-29T12:00:00Z",
    "version": "1.0.0"
  }
}
```

Ответ с ошибкой:

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid payload",
    "details": {}
  },
  "meta": {
    "timestamp": "2026-03-29T12:00:00Z",
    "version": "1.0.0"
  }
}
```

## Публичные endpoint'ы

### `GET /`

Метаданные приложения.

### `GET /health`

Health-check.

### `GET /api/v1/demo/candidates`

Список demo-fixtures.

### `GET /api/v1/demo/candidates/{slug}`

Чтение одного demo-сценария.

### `POST /api/v1/demo/candidates/{slug}/run`

Прогон demo-сценария через живой pipeline.

### `POST /api/v1/candidates/intake`

Валидация и сохранение входного payload кандидата.

Актуальные правила входного этапа:

- `contacts.email` обязателен
- `content.video_url` обязателен
- `content.essay_text` опционален
- `content.transcript_text` опционален и может заменить эссе в downstream-логике

### `POST /api/v1/pipeline/submit`

Запускает синхронный аналитический pipeline:

`Input Intake -> optional ASR -> Privacy -> Profile -> Extraction -> Scoring -> Explanation`

### `POST /api/v1/pipeline/batch`

Запускает тот же flow для нескольких payload'ов.

## Auth endpoint'ы

### `POST /api/v1/auth/login`

Создает session cookie.

Пример:

```json
{
  "email": "reviewer@invisionu.local",
  "password": "333333"
}
```

### `POST /api/v1/auth/logout`

Завершает текущую сессию.

### `GET /api/v1/auth/me`

Возвращает текущего авторизованного пользователя.

## Admin endpoint'ы

Все endpoint'ы ниже требуют роль `admin`.

### `GET /api/v1/admin/users`

Список пользователей.

### `POST /api/v1/admin/users`

Создание пользователя.

### `PATCH /api/v1/admin/users/{user_id}`

Обновление роли, имени, пароля или флага активности.

### `GET /api/v1/audit/feed?limit=100`

Глобальный журнал действий.

## Endpoint'ы рабочей зоны комиссии

Все endpoint'ы ниже требуют session cookie и одну из ролей:

- `reviewer`
- `chair`
- `admin` для read-only маршрутов

### `GET /api/v1/dashboard/stats`

Сводные метрики рабочей зоны комиссии.

Роли:

- `reviewer`
- `chair`
- `admin`

### `GET /api/v1/dashboard/candidates`

Список обработанных кандидатов для рейтинга.

Роли:

- `reviewer`
- `chair`
- `admin`

### `GET /api/v1/dashboard/candidate-pool`

Живой пул кандидатов, разделенный на:

- `raw`
- `processed`

Роли:

- `reviewer`
- `chair`
- `admin`

### `GET /api/v1/dashboard/candidates/{candidate_id}`

Детальная карточка кандидата:

- безопасная identity projection
- оценка кандидата
- explanation output
- безопасный source content
- история действий комиссии
- состояние видимости по ролям

Роли:

- `reviewer`
- `chair`
- `admin`

### `POST /api/v1/dashboard/candidates/{candidate_id}/viewed`

Фиксирует, что текущий член комиссии или председатель открыл карточку кандидата.

Роли:

- `reviewer`
- `chair`

### `POST /api/v1/dashboard/candidates/{candidate_id}/decision`

Сохраняет рекомендацию члена комиссии или итоговое решение председателя для текущего авторизованного пользователя.

Тело запроса:

```json
{
  "new_status": "RECOMMEND",
  "comment": "Кандидат демонстрирует устойчивую инициативу и ясное соответствие программе."
}
```

Поведение:

- для `reviewer` создается приватная рекомендация, привязанная к `user.id`
- для `chair` сохраняется итоговое решение председателя и обновляется итоговый статус кандидата

### `GET /api/v1/audit/feed`

Административный журнал review- и system-событий.

Роли:

- `admin`

## Примечание по названиям этапов

В коде по-прежнему сохраняются внутренние `m*` package names. В API-документации используются публичные stage names, чтобы аналитический flow и workflow комиссии были описаны понятнее.
