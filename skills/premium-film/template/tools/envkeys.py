"""Reads API keys from the environment or, failing that, from the project's git-ignored .env (KEY=value lines).
Never print a key."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def key(name):
    if os.environ.get(name):
        return os.environ[name]
    p = os.path.join(ROOT, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if line.startswith(f"{name}=") and line.split("=", 1)[1].strip():
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None
