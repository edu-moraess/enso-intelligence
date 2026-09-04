# External Data Foundation

The ENSO Data Foundation is scheduled outside GitHub Actions using a Cloudflare Worker Cron Trigger.

## Architecture

```text
NOAA CPC → Cloudflare Worker → validation/versioning → GitHub Contents API → data/foundation/
```

The Worker does not clone or host the private repository. It fetches the three official NOAA CPC products directly and publishes only validated, content-addressed snapshots.

## Secret

Create a Cloudflare Worker secret named `GITHUB_TOKEN`.

The token should be a fine-grained GitHub token restricted to `edu-moraess/enso-intelligence` and limited to the minimum Contents permission needed to create/update `data/foundation/` files.

Never commit the token or put it in `wrangler.jsonc`.

## Deploy

From `cloudflare/`:

```bash
npx wrangler secret put GITHUB_TOKEN
npx wrangler deploy
```

The configured Cron Trigger runs daily at `03:17 UTC` (`00:17 BRT`). Cloudflare Cron Triggers use UTC.

## Security model

- Repository remains private.
- No repository clone is required by the Worker.
- GitHub credential is a Cloudflare encrypted secret.
- Non-secret configuration is versioned in `wrangler.jsonc`.
- Only validated NOAA-derived snapshots are published.
- The Worker has no access to the Streamlit runtime or application secrets.
