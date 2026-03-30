# Frontend

Фронтенд проекта `inVision U` на `Next.js 14`.

## Что нужно

- `Node.js` 18+
- `npm`

## Быстрый запуск

```bash
cd frontend
npm install
npm run dev
```

После запуска приложение будет доступно по адресу [http://localhost:3000](http://localhost:3000).

## Подключение к backend

По умолчанию фронтенд ожидает API на `http://localhost:8000`.

Если нужен другой адрес, создай файл `.env.local` в папке `frontend`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
REVIEWER_API_KEY=change-me-reviewer-key
```

`REVIEWER_API_KEY` используется только на серверной стороне Next.js для proxy-маршрута `/api/backend/*`, поэтому reviewer key не уходит в браузер.

## Полезные команды

```bash
npm run dev
npm run build
npm run start
npm run test:e2e
npm run test:e2e:install
```

## Docker

Полный стек теперь можно поднять из корня репозитория:

```bash
cd ..
./scripts/stack.sh up
```

После старта:

- фронтенд: `http://localhost:3000`
- backend: `http://localhost:8000`

## Примечание

Reviewer-экраны используют живые backend-данные через встроенный proxy.

Для smoke e2e:

1. Подними Postgres.
2. Убедись, что `backend` зависимости установлены и миграции могут примениться.
3. Установи браузер для Playwright:

```bash
cd frontend
npm run test:e2e:install
```

4. Запусти smoke e2e:

```bash
cd frontend
npm run test:e2e
```

Playwright сам поднимет `backend` и `frontend`, но ожидает доступный Postgres на стандартных переменных окружения backend.
