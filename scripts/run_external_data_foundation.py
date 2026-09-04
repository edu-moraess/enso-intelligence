"""Run the ENSO data foundation from an external scheduler.

This runner is intentionally independent from GitHub Actions. It ingests the
live NOAA CPC datasets, persists immutable snapshots, and pushes only newly
created snapshots back to the repository.

Required environment variables:
    GITHUB_TOKEN: fine-grained token with Contents: Read and write on this repo.
Optional:
    GITHUB_REPOSITORY: owner/name. Defaults to edu-moraess/enso-intelligence.
    GIT_BRANCH: branch to update. Defaults to main.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from update_data_foundation import main as update_foundation


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = os.getenv("GITHUB_REPOSITORY", "edu-moraess/enso-intelligence")
BRANCH = os.getenv("GIT_BRANCH", "main")
TOKEN = os.getenv("GITHUB_TOKEN")


def run(*args: str) -> None:
    subprocess.run(args, cwd=ROOT, check=True)


def main() -> None:
    if not TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required for external snapshot publishing")

    run("git", "fetch", "origin", BRANCH, "--depth=1")
    run("git", "checkout", BRANCH)
    run("git", "reset", "--hard", f"origin/{BRANCH}")

    # Live NOAA ingestion and validation. No archive is used as a fallback.
    update_foundation()

    run("git", "add", "-f", "data/foundation")
    status = subprocess.run(
        ("git", "diff", "--cached", "--quiet"), cwd=ROOT, check=False
    )
    if status.returncode == 0:
        print("No new NOAA snapshot to publish.")
        return
    if status.returncode != 1:
        raise RuntimeError("Unable to determine staged snapshot changes")

    run("git", "config", "user.name", "enso-data-foundation-bot")
    run("git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    run("git", "commit", "-m", "data: update NOAA ENSO foundation snapshots")

    remote = f"https://x-access-token:{TOKEN}@github.com/{REPOSITORY}.git"
    run("git", "push", remote, f"HEAD:{BRANCH}")
    print("NOAA ENSO foundation snapshots published successfully.")


if __name__ == "__main__":
    main()
