"""Load .env from project root (gitignored)."""
from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_project_env() -> None:
    env_path = PROJECT_ROOT / ".env"
    try:
        from dotenv import load_dotenv

        load_dotenv(env_path)
    except ImportError:
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def get_openai_api_key() -> str:
    load_project_env()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key or key == "your_openai_key_here":
        raise SystemExit(
            "OPENAI_API_KEY missing. Copy .env.example to .env and add your key (never commit .env)."
        )
    return key


def get_anthropic_api_key() -> str:
    load_project_env()
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key or key == "your_anthropic_key_here":
        raise SystemExit(
            "ANTHROPIC_API_KEY missing. Add it to .env (never commit .env) "
            "to use --provider anthropic."
        )
    return key


def env_bool(name: str, default: bool = True) -> bool:
    load_project_env()
    raw = os.environ.get(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")
