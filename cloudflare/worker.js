const FOUNDATION_VERSION = "1.1";

const DATASETS = {
  roni: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
    required: ["date", "roni"],
  },
  oni: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    required: ["date", "oni"],
  },
  weekly_nino: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for",
    required: ["date", "nino12", "nino3", "nino34", "nino4"],
  },
  soi: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/soi",
    required: ["date", "year", "month", "soi"],
  },
};

function sha256Hex(input) {
  return crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(input)
  ).then(buffer =>
    [...new Uint8Array(buffer)]
      .map(b => b.toString(16).padStart(2, "0"))
      .join("")
  );
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text)
    ? `"${text.replace(/"/g, '""')}"`
    : text;
}

function toCsv(rows, columns) {
  return [
    columns.join(","),
    ...rows.map(row =>
      columns.map(column => csvEscape(row[column])).join(",")
    ),
  ].join("\n") + "\n";
}

function parseRoni(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const match = line.match(
      /^\s*(\d{4})\s+(\d{1,2})\s+([+-]?\d+(?:\.\d+)?)/
    );

    if (!match) continue;

    const [, year, month, value] = match;

    rows.push({
      date: `${year}-${String(month).padStart(2, "0")}-15`,
      roni: Number(value),
    });
  }

  if (!rows.length) {
    throw new Error("RONI parser returned no observations");
  }

  return rows;
}

function parseOni(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const match = line.match(
      /^\s*(\d{4})\s+([A-Z]{3})\s+([+-]?\d+(?:\.\d+)?)/
    );

    if (!match) continue;

    const [, year, monthName, value] = match;

    const months = {
      JAN: 1,
      FEB: 2,
      MAR: 3,
      APR: 4,
      MAY: 5,
      JUN: 6,
      JUL: 7,
      AUG: 8,
      SEP: 9,
      OCT: 10,
      NOV: 11,
      DEC: 12,
    };

    const month = months[monthName];

    if (!month) continue;

    rows.push({
      date: `${year}-${String(month).padStart(2, "0")}-15`,
      oni: Number(value),
    });
  }

  if (!rows.length) {
    throw new Error("ONI parser returned no observations");
  }

  return rows;
}

function parseWeeklyNino(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const match = line.match(
      /^\s*(\d{4})\s+(\d{1,2})\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)/
    );

    if (!match) continue;

    const [, year, week, nino12, nino3, nino34, nino4] = match;

    rows.push({
      date: `${year}-01-01`,
      week: Number(week),
      nino12: Number(nino12),
      nino3: Number(nino3),
      nino34: Number(nino34),
      nino4: Number(nino4),
    });
  }

  if (!rows.length) {
    throw new Error("Weekly Niño parser returned no observations");
  }

  return rows;
}

function parseSoi(text) {
  const lines = text.split(/\r?\n/);

  const headerIndex = lines.findIndex(line =>
    /^\s*YEAR\s+JAN\s+FEB/i.test(line)
  );

  if (headerIndex === -1) {
    throw new Error("SOI header not found");
  }

  const rows = [];

  for (const line of lines.slice(headerIndex + 1)) {
    const parts = line.trim().split(/\s+/);

    if (!/^\d{4}$/.test(parts[0] ?? "")) {
      continue;
    }

    const year = Number(parts[0]);
    const values = parts.slice(1, 13);

    if (values.length < 12) {
      continue;
    }

    values.forEach((raw, index) => {
      const value = Number(raw);

      if (!Number.isFinite(value) || value <= -999) {
        return;
      }

      rows.push({
        date: `${year}-${String(index + 1).padStart(2, "0")}-15`,
        year,
        month: index + 1,
        soi: value,
      });
    });
  }

  if (!rows.length) {
    throw new Error("SOI parser returned no observations");
  }

  return rows;
}

function validateRows(rows, required) {
  if (!Array.isArray(rows) || rows.length === 0) {
    throw new Error("Dataset contains no rows");
  }

  for (const column of required) {
    if (!(column in rows[0])) {
      throw new Error(`Missing required column: ${column}`);
    }
  }
}

async function publishDataset(env, name, rows, columns) {
  validateRows(rows, columns);

  const csv = toCsv(rows, columns);
  const digest = await sha256Hex(csv);
  const snapshotId = digest.slice(0, 16);

  const basePath = `data/foundation/${name}`;
  const snapshotPath = `${basePath}/${snapshotId}.csv`;
  const manifestPath = `${basePath}/manifest.jsonl`;

  const snapshotResponse = await fetch(
    `https://api.github.com/repos/${env.GITHUB_REPOSITORY}/contents/${snapshotPath}`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        "Content-Type": "application/json",
        "User-Agent": "enso-data-foundation",
      },
      body: JSON.stringify({
        message: `data: publish ${name} snapshot ${snapshotId}`,
        content: btoa(csv),
        branch: env.GIT_BRANCH,
      }),
    }
  );

  if (!snapshotResponse.ok && snapshotResponse.status !== 422) {
    throw new Error(
      `GitHub snapshot publish failed: ${snapshotResponse.status}`
    );
  }

  const manifestEntry = JSON.stringify({
    dataset: name,
    snapshot_id: snapshotId,
    sha256: digest,
    rows: rows.length,
    retrieved_at: new Date().toISOString(),
    foundation_version: FOUNDATION_VERSION,
  }) + "\n";

  let existingManifest = "";

  const manifestGet = await fetch(
    `https://api.github.com/repos/${env.GITHUB_REPOSITORY}/contents/${manifestPath}?ref=${env.GIT_BRANCH}`,
    {
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        "User-Agent": "enso-data-foundation",
      },
    }
  );

  let manifestSha;

  if (manifestGet.ok) {
    const data = await manifestGet.json();
    manifestSha = data.sha;
    existingManifest = atob(data.content.replace(/\n/g, ""));
  }

  const updatedManifest = existingManifest + manifestEntry;

  const manifestResponse = await fetch(
    `https://api.github.com/repos/${env.GITHUB_REPOSITORY}/contents/${manifestPath}`,
    {
      method: "PUT",
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        "Content-Type": "application/json",
        "User-Agent": "enso-data-foundation",
      },
      body: JSON.stringify({
        message: `data: update ${name} manifest`,
        content: btoa(updatedManifest),
        branch: env.GIT_BRANCH,
        ...(manifestSha ? { sha: manifestSha } : {}),
      }),
    }
  );

  if (!manifestResponse.ok) {
    throw new Error(
      `GitHub manifest publish failed: ${manifestResponse.status}`
    );
  }

  return {
    snapshot_id: snapshotId,
    sha256: digest,
    rows: rows.length,
  };
}

async function run(env) {
  const results = {};
  const errors = {};

  for (const [name, config] of Object.entries(DATASETS)) {
    try {
      const response = await fetch(config.url, {
        headers: {
          "User-Agent": "enso-data-foundation",
        },
      });

      if (!response.ok) {
        throw new Error(
          `NOAA request failed: ${response.status} ${response.statusText}`
        );
      }

      const text = await response.text();

      let rows;

      if (name === "roni") {
        rows = parseRoni(text);
      } else if (name === "oni") {
        rows = parseOni(text);
      } else if (name === "weekly_nino") {
        rows = parseWeeklyNino(text);
      } else if (name === "soi") {
        rows = parseSoi(text);
      }

      const columns = config.required;

      results[name] = await publishDataset(
        env,
        name,
        rows,
        columns
      );
    } catch (error) {
      const message =
        error instanceof Error ? error.message : String(error);

      console.error(`Dataset ${name} failed: ${message}`);

      errors[name] = message;
    }
  }

  console.log(
    JSON.stringify({
      foundation_version: FOUNDATION_VERSION,
      retrieved_at: new Date().toISOString(),
      results,
      errors,
    })
  );

  return { results, errors };
}

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(run(env));
  },

  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return new Response(
        JSON.stringify({
          status: "ok",
          foundation_version: FOUNDATION_VERSION,
        }),
        {
          headers: {
            "Content-Type": "application/json",
          },
        }
      );
    }

    return new Response("ENSO Data Foundation", {
      status: 200,
    });
  },
};
