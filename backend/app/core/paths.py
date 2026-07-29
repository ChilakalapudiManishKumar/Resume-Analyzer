"""
Resolves the path to the project's shared `data/` folder (skills taxonomy,
role-skill map, skill resources, interview questions).

Locally, this folder lives two levels above `backend/` (a sibling of it).
In Docker, the container's directory layout is different — the Dockerfile
copies `data/` in at build time as `/app/data` — so we prefer an explicit
APP_DATA_DIR env var when set, and only fall back to the relative-path
guess for local (non-container) development.
"""
import os
from pathlib import Path


def get_data_dir() -> Path:
    env_override = os.environ.get("APP_DATA_DIR")
    if env_override:
        return Path(env_override)
    # backend/app/core/paths.py -> parents[2] = backend/ -> parents[3] = project root
    return Path(__file__).resolve().parents[3] / "data"
