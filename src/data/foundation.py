"""Lean data foundation for NOAA-derived ENSO observations.

The foundation is deliberately storage-light: it keeps canonical CSV snapshots
and a manifest using only the Python standard library and pandas. Snapshots are
archival metadata, never a fallback source for the live observatory.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional, Tuple

import pandas as pd


FOUNDATION_VERSION = "1.2"
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "foundation"
