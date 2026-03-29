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
```

## Полезные команды

```bash
npm run dev
npm run build
npm run start
```

## Примечание

Часть экранов сейчас может работать на мок-данных, поэтому UI можно запускать отдельно даже без полного backend-контура.
