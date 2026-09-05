"""Audit GODAS monthly file availability from NOAA's public FTP index.

The NOAA CPC monthly GODAS directory exposes a file-level ``Last modified``
time. This module treats that timestamp as evidence of when the file was
present on the public distribution server, not as a claim about the exact
internal production timestamp.

For historical files that were bulk-relocated/re-hosted (for example, files
whose server timestamp predates the relocation-era boundary), the timestamp
is intentionally rejected as a publication-time proxy.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Iterable

GODAS_MONTHLY_INDEX = "https://www.ftp.cpc.ncep.noaa.gov/godas/monthly/"
_FILE_RE = re.compile(
    r"godas\.M\.(?P<year>\d{4})(?P<month>\d{2})\.grb\s+"
    r"(?P<day>\d{2})-(?P<mon>[A-Za-z]{3})-(?P<file_year>\d{4})\s+"
    r"(?P<hour>\d{2}):(?P<minute>\d{2})"
)

# The NOAA directory was relocated in 2024. Server timestamps from the bulk
# relocation are not historical release timestamps and must not be promoted
# to information-time evidence.
RELOCATION_CUTOFF = datetime(2024, 12, 1, tzinfo=timezone.utc)


@dataclass(frozen=True)
class GodasFileAvailability:
    year: int
    month: int
    available_at: datetime | None
    evidence_url: str
    status: str
    notes: str


def parse_monthly_index(text: str, *, evidence_url: str = GODAS_MONTHLY_INDEX) -> list[GodasFileAvailability]:
    """Parse NOAA FTP directory rows into conservative availability records."""
    records: list[GodasFileAvailability] = []
    for match in _FILE_RE.finditer(text):
        year = int(match.group("year"))
        month = int(match.group("month"))
        timestamp = datetime.strptime(
            f"{match.group('day')}-{match.group('mon')}-{match.group('file_year')} "
            f"{match.group('hour')}:{match.group('minute')}",
            "%d-%b-%Y %H:%M",
        ).replace(tzinfo=timezone.utc)

        if timestamp < RELOCATION_CUTOFF:
            records.append(
                GodasFileAvailability(
                    year,
                    month,
                    None,
                    evidence_url,
                    "rejected",
                    "Server timestamp predates the relocation-era cutoff and is not treated as historical publication evidence.",
                )
            )
        else:
            records.append(
                GodasFileAvailability(
                    year,
                    month,
                    timestamp,
                    evidence_url,
                    "server_present",
                    "Timestamp records when the monthly file was present on NOAA's public FTP distribution index.",
                )
            )
    return sorted(records, key=lambda r: (r.year, r.month))


def availability_for_month(records: Iterable[GodasFileAvailability], year: int, month: int) -> GodasFileAvailability:
    """Return one month or fail explicitly when no auditable record exists."""
    for record in records:
        if record.year == year and record.month == month:
            return record
    raise KeyError(f"No auditable GODAS monthly file record for {year:04d}-{month:02d}")
