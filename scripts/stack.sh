#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.yml"

if docker compose version >/dev/null 2>&1; then
  COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE_CMD=(docker-compose)
else
  echo "Docker Compose is not available. Install Docker Desktop or docker-compose first." >&2
  exit 1
fi

ACTION="${1:-up}"
if [[ $# -gt 0 ]]; then
  shift
fi

case "$ACTION" in
  up)
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up --build "$@"
    ;;
  down)
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" down "$@"
    ;;
  reset)
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" down -v "$@"
    ;;
  logs)
    "${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" logs -f "$@"
    ;;
  *)
    echo "Usage: ./scripts/stack.sh {up|down|reset|logs} [extra compose args]" >&2
    exit 1
    ;;
esac
