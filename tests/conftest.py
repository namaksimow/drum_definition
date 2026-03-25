from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_ROOT = REPO_ROOT / "backend"
ML_SERVICE_SRC = REPO_ROOT / "ml-service" / "src"

for path in (BACKEND_ROOT, ML_SERVICE_SRC):
    value = str(path)
    if value not in sys.path:
        sys.path.insert(0, value)

