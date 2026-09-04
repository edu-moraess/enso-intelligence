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


FOUNDATION_VERSION = "1.1"
DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "foundation"


@dataclass(frozen=True)
class ValidationResult:
    """Machine-readable validation outcome for a canonical dataset."""

    valid: bool
    rows: int
    columns: tuple[str, ...]
    duplicate_rows: int
    duplicate_dates: int
    missing_required: tuple[str, ...]
    non_numeric_values: tuple[str, ...]
    date_monotonic: bool
    message: str


@dataclass(frozen=True)
class SnapshotMetadata:
    """Provenance for one immutable content-addressed snapshot."""

    dataset: str
    source: str
    source_url: str
    retrieved_at: str
    snapshot_id: str
    rows: int
    start: Optional[str]
    end: Optional[str]
    validation: ValidationResult


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonicalize(df: pd.DataFrame, required_columns: tuple[str, ...]) -> pd.DataFrame:
    """Return a deterministic canonical dataframe without changing observations."""
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    work = df.copy()
    if "date" in work.columns:
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        work = work.sort_values("date", kind="mergesort")
    else:
        work = work.sort_index(kind="mergesort")
    return work.reset_index(drop=True)


def validate_dataset(df: pd.DataFrame, required_columns: tuple[str, ...]) -> ValidationResult:
    """Validate structure, dates, duplicates and numeric fields before archiving."""
    missing = tuple(column for column in required_columns if column not in df.columns)
    work = df.copy()

    duplicate_rows = int(work.duplicated().sum())
    duplicate_dates = 0
    date_monotonic = True
    if "date" in work.columns:
        dates = pd.to_datetime(work["date"], errors="coerce")
        duplicate_dates = int(dates.duplicated().sum())
        date_monotonic = bool(dates.notna().all() and dates.is_monotonic_increasing)

    numeric_columns = [c for c in required_columns if c != "date" and c in work.columns]
    non_numeric = tuple(
        column for column in numeric_columns
        if not pd.to_numeric(work[column], errors="coerce").notna().all()
    )

    valid = not missing and duplicate_rows == 0 and duplicate_dates == 0 and date_monotonic and not non_numeric
    if valid:
        message = "OK"
    else:
        reasons = []
        if missing:
            reasons.append("missing required columns")
        if duplicate_rows:
            reasons.append("duplicate rows")
        if duplicate_dates:
            reasons.append("duplicate dates")
        if not date_monotonic:
            reasons.append("invalid or non-monotonic dates")
        if non_numeric:
            reasons.append("non-numeric values")
        message = "; ".join(reasons)

    return ValidationResult(
        valid=valid,
        rows=len(work),
        columns=tuple(work.columns),
        duplicate_rows=duplicate_rows,
        duplicate_dates=duplicate_dates,
        missing_required=missing,
        non_numeric_values=non_numeric,
        date_monotonic=date_monotonic,
        message=message,
    )


def _snapshot_id(df: pd.DataFrame) -> str:
    """Create a stable SHA-256 identifier from canonical CSV content."""
    csv_bytes = df.to_csv(index=False, date_format="%Y-%m-%dT%H:%M:%S").encode("utf-8")
    return hashlib.sha256(csv_bytes).hexdigest()[:16]


def persist_snapshot(
    df: pd.DataFrame,
    *,
    dataset: str,
    source: str,
    source_url: str,
    required_columns: tuple[str, ...],
    root: Path = DEFAULT_ROOT,
) -> SnapshotMetadata:
    """Validate and persist an immutable content-addressed CSV snapshot."""
    canonical = canonicalize(df, required_columns)
    validation = validate_dataset(canonical, required_columns)
    if not validation.valid:
        raise ValueError(f"Dataset validation failed: {validation.message}")

    snapshot_id = _snapshot_id(canonical)
    dataset_dir = root / dataset
    dataset_dir.mkdir(parents=True, exist_ok=True)
    csv_path = dataset_dir / f"{snapshot_id}.csv"
    if not csv_path.exists():
        canonical.to_csv(csv_path, index=False, date_format="%Y-%m-%dT%H:%M:%S")

    metadata = SnapshotMetadata(
        dataset=dataset,
        source=source,
        source_url=source_url,
        retrieved_at=_utc_iso(),
        snapshot_id=snapshot_id,
        rows=len(canonical),
        start=str(canonical["date"].min()) if "date" in canonical.columns else None,
        end=str(canonical["date"].max()) if "date" in canonical.columns else None,
        validation=validation,
    )
    manifest_path = dataset_dir / "manifest.jsonl"
    existing = manifest_path.read_text(encoding="utf-8").splitlines() if manifest_path.exists() else []
    known_ids = {json.loads(line)["snapshot_id"] for line in existing if line.strip()}
    if snapshot_id not in known_ids:
        with manifest_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(metadata), sort_keys=True) + "\n")
    return metadata


def ingest_and_archive(
    loader: Callable[[], Tuple[Optional[pd.DataFrame], object]],
    *,
    dataset: str,
    required_columns: tuple[str, ...],
    root: Path = DEFAULT_ROOT,
) -> Tuple[Optional[pd.DataFrame], object, Optional[SnapshotMetadata]]:
    """Run an existing NOAA loader and archive only successful live observations.

    Cached snapshots are intentionally not returned on failure: the observatory
    must never silently substitute archived data for unavailable live NOAA data.
    """
    df, meta = loader()
    if df is None or df.empty:
        return df, meta, None

    snapshot = persist_snapshot(
        df,
        dataset=dataset,
        source=getattr(meta, "source", "NOAA CPC"),
        source_url=getattr(meta, "url", ""),
        required_columns=required_columns,
        root=root,
    )
    return df, meta, snapshot
