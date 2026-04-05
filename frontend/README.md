# Frontend

`invisionU` frontend on `Next.js 14` for the admissions committee workflow with session auth, RBAC, localized review screens, candidate upload, and committee decisions.

## Requirements

- `Node.js` 18+
- `npm`
- running backend API

## Quick start

```bash
cd frontend
npm install
npm run dev
```

App URL: [http://localhost:3000](http://localhost:3000)

The root route `/` redirects to `/login`.

## Backend connection

By default the frontend talks to `http://localhost:8000`.

If needed, create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
BACKEND_URL=http://localhost:8000
```

Important:

- browser requests go through the built-in proxy at `frontend/src/app/api/backend/[...path]/route.ts`
- the proxy rewrites `/api/backend/*` to backend `/api/v1/*`
- auth uses session cookies and backend role checks
- committee visibility is determined on the backend by RBAC

## Main routes

- `/login` - login screen with demo accounts
- `/candidates` - live candidate pool split into unprocessed and processed candidates
- `/dashboard` - processed candidate ranking
- `/dashboard/[id]` - candidate detail, committee recommendation, chair decision
- `/upload` - video-first candidate input via form or JSON plus demo scenario launcher
- `/admin/users` - admin-only user management
- `/audit` - admin-only audit feed

## Frontend surfaces by stage

- `Input Intake` - represented by `/upload`
- `Review Workspace` - represented by `/candidates`, `/dashboard`, and `/dashboard/[id]`
- `Administration` - represented by `/admin/users`
- `Audit Review` - represented by `/audit`

## Input rules

- required: `personal.first_name`, `personal.last_name`, `personal.date_of_birth`
- required: `contacts.email`
- required: `content.video_url`
- optional: `content.essay_text`
- optional: `content.transcript_text`
- if `essay_text` is empty, the downstream narrative can be built from transcript text

## Useful commands

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

From the repository root:

```bash
./scripts/stack.sh up
```

Services:

- frontend: `http://localhost:3000`
- backend: `http://localhost:8000`
- postgres: `localhost:5432`

## E2E

Playwright config lives in `frontend/playwright.config.ts`.

It starts:

- backend with Alembic migrations and `uvicorn`
- frontend with `npm run dev -- --hostname 127.0.0.1 --port 3000`

Before running E2E:

1. Start PostgreSQL.
2. Make sure backend dependencies are installed.
3. Install browsers:

```bash
cd frontend
npm run test:e2e:install
```

4. Run tests:

```bash
cd frontend
npm run test:e2e
```
