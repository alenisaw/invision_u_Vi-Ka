# API Reference

## Overview

Backend base URL:

`http://localhost:8000`

Frontend proxy base URL:

`http://localhost:3000/api/backend/*`

The Next.js proxy rewrites `/api/backend/*` to backend `/api/v1/*`.

Authentication model:

- login creates an HTTP-only session cookie
- protected routes use backend session auth
- role access is enforced with RBAC

The public documentation uses stage names:

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

Successful response:

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

Error response:

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

## Public endpoints

### `GET /`

Application metadata.

### `GET /health`

Health response.

### `GET /api/v1/demo/candidates`

List demo fixtures.

### `GET /api/v1/demo/candidates/{slug}`

Read one demo fixture.

### `POST /api/v1/demo/candidates/{slug}/run`

Run a demo fixture through the live pipeline.

### `POST /api/v1/candidates/intake`

Validate and persist a candidate input payload.

Current input rules:

- `contacts.email` is required
- `content.video_url` is required
- `content.essay_text` is optional
- `content.transcript_text` is optional and can replace essay text downstream

### `POST /api/v1/pipeline/submit`

Run the synchronous analytical pipeline:

`Input Intake -> optional ASR -> Privacy -> Profile -> Extraction -> Scoring -> Explanation`

### `POST /api/v1/pipeline/batch`

Run the same flow for multiple payloads.

## Auth endpoints

### `POST /api/v1/auth/login`

Create a session cookie.

Request body:

```json
{
  "email": "reviewer@invisionu.local",
  "password": "333333"
}
```

### `POST /api/v1/auth/logout`

Invalidate the current session.

### `GET /api/v1/auth/me`

Return the current authenticated user.

## Admin endpoints

All endpoints below require the `admin` role.

### `GET /api/v1/admin/users`

List users.

### `POST /api/v1/admin/users`

Create a user.

### `PATCH /api/v1/admin/users/{user_id}`

Update a user role, password, name, or active flag.

### `GET /api/v1/audit/feed?limit=100`

Global audit feed.

## Review workspace endpoints

All endpoints below require a session cookie and one of these roles:

- `reviewer`
- `chair`
- `admin` for read access where stated

### `GET /api/v1/dashboard/stats`

Review workspace summary metrics.

Roles:

- `reviewer`
- `chair`
- `admin`

### `GET /api/v1/dashboard/candidates`

Processed candidate ranking list.

Roles:

- `reviewer`
- `chair`
- `admin`

### `GET /api/v1/dashboard/candidate-pool`

Live candidate pool split into:

- `raw`
- `processed`

Roles:

- `reviewer`
- `chair`
- `admin`

### `GET /api/v1/dashboard/candidates/{candidate_id}`

Candidate detail response with:

- candidate identity projection
- candidate score
- explanation output
- safe source content
- committee action log
- committee visibility state

Roles:

- `reviewer`
- `chair`
- `admin`

### `POST /api/v1/dashboard/candidates/{candidate_id}/viewed`

Record that the current reviewer or chair opened the candidate.

Roles:

- `reviewer`
- `chair`

### `POST /api/v1/dashboard/candidates/{candidate_id}/decision`

Submit a committee recommendation or chair decision for the current authenticated user.

Request body:

```json
{
  "new_status": "RECOMMEND",
  "comment": "The candidate demonstrates sustained initiative and a clear fit for the program."
}
```

Behavior:

- for `reviewer`, this stores a private committee recommendation tied to `user.id`
- for `chair`, this stores the final chair decision and updates the persisted candidate status

### `GET /api/v1/audit/feed`

Administrative review and audit feed.

Roles:

- `admin`

## Notes on stage naming

Current code packages still use internal `m*` names. Public API documentation uses runtime stage names to describe the analytical flow and committee workflow more clearly.
