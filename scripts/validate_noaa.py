from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.noaa.cpc import fetch_nino_indices, fetch_oni
from src.noaa.roni import fetch_roni


def main() -> None:
    checks = []
    for label, fetcher, expected in (
        ("RONI", fetch_roni, "roni"),
        ("ONI", fetch_oni, "oni"),
        ("Niño", fetch_nino_indices, "nino34_ssta"),
    ):
        frame, meta = fetcher(timeout=30)
        ok = frame is not None and not frame.empty and expected in frame.columns and meta.status == "ok"
        checks.append((label, ok, meta.status, meta.n_records, meta.endpoint))
        if frame is not None:
            print(f"{label}: status={meta.status} records={len(frame)} columns={list(frame.columns)} latest={frame.iloc[-1].to_dict()}")
        else:
            print(f"{label}: status={meta.status} records=0 message={meta.message}")

    class OfflineResponse:
        def raise_for_status(self):
            raise RuntimeError("offline")

    with patch("src.noaa.roni.requests.get", side_effect=__import__("requests").RequestException("offline")):
        frame, meta = fetch_roni(timeout=1)
        outage_ok = frame is None and meta.status == "unavailable" and meta.n_records == 0
        print(f"outage handling: status={meta.status} message={meta.message}")
        checks.append(("NOAA outage", outage_ok, meta.status, meta.n_records, meta.endpoint))

    if not all(ok for _, ok, *_ in checks):
        raise SystemExit("NOAA validation failed: " + repr(checks))
    print("NOAA validation: PASS")


if __name__ == "__main__":
    main()
