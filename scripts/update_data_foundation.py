"""Update durable NOAA-derived snapshots for the ENSO data foundation."""

from __future__ import annotations

from src.data.foundation import persist_snapshot
from src.noaa.cpc import fetch_nino_indices as fetch_live_nino
from src.noaa.cpc import fetch_oni as fetch_live_oni
from src.noaa.roni import fetch_roni as fetch_live_roni


def ingest(fetcher, dataset: str, required_columns: tuple[str, ...]) -> None:
    df, meta = fetcher()
    if df is None or df.empty:
        raise RuntimeError(f"{dataset}: live NOAA dataset unavailable")
    snapshot = persist_snapshot(
        df,
        dataset=dataset,
        source=meta.source,
        source_url=meta.url,
        required_columns=required_columns,
    )
    print(f"{dataset}: snapshot {snapshot.snapshot_id} · {snapshot.rows} rows")


def main() -> None:
    ingest(fetch_live_roni, "roni", ("date", "season", "year", "roni"))
    ingest(fetch_live_oni, "oni", ("date", "season", "year", "oni"))
    ingest(
        fetch_live_nino,
        "weekly_nino",
        (
            "date",
            "nino12_sst", "nino12",
            "nino3_sst", "nino3",
            "nino34_sst", "nino34",
            "nino4_sst", "nino4",
        ),
    )


if __name__ == "__main__":
    main()
