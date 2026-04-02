# Frontend

Фронтенд `inVision U` на `Next.js 14` для reviewer workflow: локализованный рейтинг, live candidate pool, карточка кандидата, сравнение, video-first загрузка, shortlist и аудит.

## Что нужно

- `Node.js` 18+
- `npm`
- доступный backend API
- доступный `PostgreSQL`, если запускаются e2e и локальный backend

## Быстрый запуск

```bash
cd frontend
npm install
npm run dev
```

Приложение поднимается на [http://localhost:3000](http://localhost:3000).
Маршрут `/` перенаправляет на `/dashboard`.

## Подключение к backend

По умолчанию frontend работает с backend на `http://localhost:8000`.

Если нужен другой адрес, создай `.env.local` в папке `frontend`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
REVIEWER_API_KEY=change-me-reviewer-key
```

Что важно:

- browser-запросы идут через встроенный proxy `frontend/src/app/api/backend/[...path]/route.ts`
- proxy проксирует `/api/backend/*` в backend `/api/v1/*`
- `REVIEWER_API_KEY` серверно прокидывается как `X-API-Key` только для reviewer-маршрутов `dashboard/*` и `audit/*`
- reviewer key не попадает в браузерный bundle

## Основные страницы

- `/dashboard` — общий рейтинг и фильтрация кандидатов
- `/dashboard/[id]` — детальная карточка кандидата, explainability и override
- `/dashboard/compare` — сравнение выбранных кандидатов по `ids`
- `/candidates` — live candidate pool с разделением на необработанные и обработанные заявки
- `/candidates/compare` — сравнение демо-кандидатов по `slugs`
- `/upload` — ручная video-first загрузка формы или JSON и запуск pipeline; demo fixtures запускаются отсюда
- `/shortlist` — shortlist view
- `/audit` — журнал reviewer-действий

## Актуальная логика intake

- обязательны `personal.first_name`, `personal.last_name`, `personal.date_of_birth`
- обязательны `contacts.email` и `content.video_url`
- `content.essay_text` опционален
- если `essay_text` пустой, narrative может быть собран из `transcript_text`
- `citizenship` в UI выбирается из списка стран

## Полезные команды

```bash
npm run dev
npm run build
npm run start
npm run lint
npm run test:e2e
npm run test:e2e:headed
npm run test:e2e:install
```

## Docker

Полный стек можно поднять из корня репозитория:

```bash
cd ..
./scripts/stack.sh up
```

После старта доступны:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`
- postgres: `localhost:5432`

## E2E

Playwright-конфиг находится в `frontend/playwright.config.ts` и сам поднимает:

- backend через `python3 -m alembic upgrade head && python3 -m uvicorn app.main:app ...`
- frontend через `npm run dev -- --hostname 127.0.0.1 --port 3000`

Перед запуском smoke e2e:

1. Подними `PostgreSQL`.
2. Убедись, что backend-зависимости установлены и миграции могут примениться.
3. Установи браузер:

```bash
cd frontend
npm run test:e2e:install
```

4. Запусти тесты:

```bash
cd frontend
npm run test:e2e
```

Если `API_KEY` не задан, Playwright использует локальный дефолт `test-reviewer-key`.
