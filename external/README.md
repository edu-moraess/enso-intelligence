# External NOAA Data Foundation Runner

This runner replaces GitHub Actions as the **scheduler/execution layer** for the ENSO Data Foundation when GitHub Actions is unavailable or account-restricted.

The repository remains the source-control and archival destination. The external service executes the existing NOAA ingestion code and publishes new content-addressed snapshots to `data/foundation/`.

## Flow

```text
External scheduler
      ↓
run_external_data_foundation.py
      ↓
Live NOAA CPC
      ↓
canonicalization + validation
      ↓
data/foundation/
      ↓
Git commit + push
```

There is **no archived-data fallback**. If NOAA ingestion or validation fails, the runner exits without publishing a snapshot.

## Environment variables

Required:

- `GITHUB_TOKEN` — fine-grained GitHub token with **Contents: Read and write** permission for `edu-moraess/enso-intelligence`.

Optional:

- `GITHUB_REPOSITORY` — defaults to `edu-moraess/enso-intelligence`.
- `GIT_BRANCH` — defaults to `main`.

## Run manually

From the repository root:

```bash
python scripts/run_external_data_foundation.py
```

The external environment must have Python 3.11+ and the project dependencies installed.

## Scheduling

The included `render.yaml` describes a cron-job deployment for an external scheduler. The cron expression is `17 3 * * *` (03:17 UTC / 00:17 BRT), matching the previous daily cadence.

The external provider is responsible for its own billing, secrets and execution limits. GitHub Actions is no longer required for this ingestion path.

## Security

Never commit `GITHUB_TOKEN`. Store it as a secret/environment variable in the external provider. Use a fine-grained token scoped only to this repository and only to the Contents permission required for snapshot publishing.
