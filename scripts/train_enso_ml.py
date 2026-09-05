"""Train and publish the production RONI +1-season ML candidate.

This script is intentionally separate from Streamlit. It consumes the canonical
Foundation snapshots, evaluates learned models with expanding walk-forward
validation, and publishes a model only when it beats the persistence baseline.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib

from src.data.foundation import load_latest_snapshot
from src.ml.benchmark import benchmark_models
from src.ml.features import build_feature_table, feature_columns
from src.noaa import ONI_REQUIRED, RONI_REQUIRED, WEEKLY_NINO_REQUIRED


def _load_optional_nino():
    try:
        return load_latest_snapshot("weekly_nino", WEEKLY_NINO_REQUIRED)[0]
    except (FileNotFoundError, KeyError, ValueError, OSError):
        return None


def train(output_dir: Path) -> dict:
    roni, roni_meta = load_latest_snapshot("roni", RONI_REQUIRED)
    oni, oni_meta = load_latest_snapshot("oni", ONI_REQUIRED)
    nino = _load_optional_nino()

    table = build_feature_table(roni, oni, nino, include_regional=False)
    results, champion = benchmark_models(table)
    result_dicts = [item.to_dict() for item in results]
    persistence = next(item for item in results if item.name == "Persistence")
    learned = [item for item in results if item.name != "Persistence"]

    output_dir.mkdir(parents=True, exist_ok=True)
    benchmark_path = output_dir / "benchmark.json"
    benchmark_path.write_text(
        json.dumps(
            {
                "target": "roni_t+1",
                "validation": "expanding_walk_forward",
                "rows": len(table),
                "roni_snapshot_id": roni_meta.snapshot_id,
                "oni_snapshot_id": oni_meta.snapshot_id,
                "results": result_dicts,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )

    if champion is None:
        print("No learned model beat persistence; production champion unchanged.")
        return {"published": False, "results": result_dicts}

    winner = min((item for item in learned if item.beats_persistence), key=lambda item: item.rmse)
    model_path = output_dir / "roni_forecast.joblib"
    metadata_path = output_dir / "metadata.json"
    joblib.dump(champion, model_path)
    metadata_path.write_text(
        json.dumps(
            {
                "status": "production",
                "model": winner.name,
                "target": "roni_t+1",
                "features": feature_columns(table),
                "feature_count": len(feature_columns(table)),
                "validation": "expanding_walk_forward",
                "validation_rmse": winner.rmse,
                "validation_mae": winner.mae,
                "persistence_rmse": persistence.rmse,
                "persistence_mae": persistence.mae,
                "n_test": winner.n_test,
                "trained_until": str(roni["date"].max().date()),
                "roni_snapshot_id": roni_meta.snapshot_id,
                "oni_snapshot_id": oni_meta.snapshot_id,
            },
            indent=2,
            sort_keys=True,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Published {winner.name}: RMSE={winner.rmse:.4f}, persistence={persistence.rmse:.4f}")
    return {"published": True, "results": result_dicts, "winner": winner.name}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("models"))
    args = parser.parse_args()
    train(args.output_dir)


if __name__ == "__main__":
    main()
