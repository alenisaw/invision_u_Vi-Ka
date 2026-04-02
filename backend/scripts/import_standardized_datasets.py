from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
from urllib import error, request


DEFAULT_DATASET_DIRS = (
    Path(r"C:\Users\alenk\Downloads\standardized_dataset\standardized_dataset"),
    Path(r"C:\Users\alenk\Downloads\standardized_dataset_ru\standardized_dataset_ru"),
)
API_URL = "http://127.0.0.1:8000/api/v1/pipeline/submit"
MOJIBAKE_MARKERS = ("Р", "С", "Ѓ", "Ђ", "џ", "вЂ", "Ñ", "Ð")


def _mojibake_score(value: str) -> int:
    return sum(value.count(marker) for marker in MOJIBAKE_MARKERS)


def maybe_fix_string(value: str) -> str:
    if not value or not any(marker in value for marker in MOJIBAKE_MARKERS):
        return value
    try:
        fixed = value.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return value
    if _mojibake_score(fixed) < _mojibake_score(value):
        return fixed
    return value


def repair_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: repair_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [repair_payload(item) for item in value]
    if isinstance(value, str):
        return maybe_fix_string(value)
    return value


def normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = repair_payload(payload)

    content = normalized.setdefault("content", {})
    if not isinstance(content, dict):
        raise ValueError("content must be an object")

    # Audio-first experiment: do not use essays from the synthetic archive.
    content["essay_text"] = None

    return normalized


def submit_payload(payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with request.urlopen(req, timeout=180) as response:
        return json.loads(response.read().decode("utf-8"))


def iter_json_files(paths: tuple[Path, ...]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix.lower() == ".json":
            files.append(path)
            continue
        if path.is_dir():
            files.extend(sorted(path.glob("*.json")))
    return sorted(files)


def main(argv: list[str]) -> int:
    roots = tuple(Path(arg) for arg in argv[1:]) or DEFAULT_DATASET_DIRS
    files = iter_json_files(roots)
    if not files:
        print("No JSON files found.", file=sys.stderr)
        return 1

    succeeded: list[tuple[str, str, str]] = []
    failed: list[tuple[str, str]] = []

    for path in files:
        try:
            raw = json.loads(path.read_text(encoding="utf-8-sig"))
            payload = normalize_payload(raw)
            result = submit_payload(payload)
            candidate_id = str(result.get("data", {}).get("candidate_id", ""))
            email = str(payload.get("contacts", {}).get("email", ""))
            succeeded.append((path.name, email, candidate_id))
            print(f"OK  {path.name} -> {candidate_id} ({email})")
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            failed.append((path.name, body))
            print(f"ERR {path.name} -> HTTP {exc.code}: {body}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            failed.append((path.name, str(exc)))
            print(f"ERR {path.name} -> {exc}", file=sys.stderr)

    print()
    print(f"Imported files: {len(files)}")
    print(f"Succeeded: {len(succeeded)}")
    print(f"Failed: {len(failed)}")

    if succeeded:
        print("Successful imports:")
        for filename, email, candidate_id in succeeded:
            print(f"- {filename}: {email} -> {candidate_id}")

    if failed:
        print("Failed imports:", file=sys.stderr)
        for filename, message in failed:
            print(f"- {filename}: {message}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
