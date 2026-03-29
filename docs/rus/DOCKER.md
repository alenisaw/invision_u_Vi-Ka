# Руководство по Docker

---

## Структура документа

- [Назначение](#назначение)
- [Docker-артефакты репозитория](#docker-артефакты-репозитория)
- [Шаблон всего репозитория](#шаблон-всего-репозитория)
- [Диаграмма 1. Контейнерная топология](#диаграмма-1-контейнерная-топология)
- [Контейнер для оценки M6](#контейнер-для-оценки-m6)

---

## Назначение

Этот документ описывает Docker-артефакты, которые сейчас есть в репозитории, и объясняет, для чего они нужны.

---

## Docker-артефакты репозитория

| Файл | Назначение |
|---|---|
| `backend/Dockerfile` | Образ серверного приложения на базе `python:3.11-slim` |
| `backend/app/modules/m6_scoring/Dockerfile.m6` | Отдельный образ для скоринга и оценки M6 |
| `docker-compose.template.yml` | Общий шаблон Docker Compose для всего репозитория |
| `docker-compose.m6.yml` | Отдельный compose-файл для оценки и notebook-сценариев M6 |

---

## Шаблон всего репозитория

Основной шаблон всего репозитория:

- `docker-compose.template.yml`

Он включает:

- `postgres`
- `backend`
- `frontend_placeholder`
- `m8_dashboard_placeholder`
- `m10_audit_placeholder`

Этот файл является стартовым шаблоном, а не готовым production-манифестом.

---

## Диаграмма 1. Контейнерная топология

```mermaid
flowchart LR
    Frontend["frontend placeholder"]
    Backend["backend service"]
    DB["postgres"]
    M8["m8_dashboard_placeholder"]
    M10["m10_audit_placeholder"]
    Net["invisionu_net"]

    Frontend --> Backend
    M8 --> Backend
    M10 --> Backend
    Backend --> DB
    Frontend --- Net
    Backend --- Net
    DB --- Net
    M8 --- Net
    M10 --- Net
```

---

## Контейнер для оценки M6

Для `M6` существует отдельный контейнерный сценарий:

- `backend/app/modules/m6_scoring/Dockerfile.m6`
- `docker-compose.m6.yml`

Он нужен для:

- синтетической оценки;
- доступа к notebook;
- изолированных экспериментов со скорингом.

---

Projet Documentation
