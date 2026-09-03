"""ENSO Intelligence — Scientific Climate Observatory."""
from __future__ import annotations

import base64
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui._observatory_payload import PAYLOAD

_SOURCE = zlib.decompress(base64.b64decode(PAYLOAD)).decode("utf-8")
exec(compile(_SOURCE, str(ROOT / "app.py"), "exec"), globals())
