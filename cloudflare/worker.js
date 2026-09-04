const FOUNDATION_VERSION = "1.1";

const DATASETS = {
  roni: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
    required: ["date", "season", "year", "roni"],
  },
  oni: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    required: ["date", "season", "year", "oni"],
  },
  weekly_nino: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for",
    required: [
      "date",
      "week",
      "nino12_sst",
      "nino12",
      "nino3_sst",
      "nino3",
      "nino34_sst",
      "nino34",
      "nino4_sst",
      "nino4",
    ],
  },
};

const MONTHS = {
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

async function sha256Hex(input) {
  const buffer = await crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(input),
  );
  return [...new Uint8Array(buffer)]
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text)
    ? `"${text.replace(/"/g, '""')}"`
    : text;
}

function toCsv(rows, columns) {
  return (
    [
      columns.join(","),
      ...rows.map((row) =>
        columns.map((column) => csvEscape(row[column])).join(","),
      ),
    ].join("\n") + "\n"
  );
}

function parseRoni(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const match = line.match(
      /^\s*(\d{4})\s+(\d{1,2})\s+([+-]?\d+(?:\.\d+)?)/,
    );
    if (!match) continue;

    const [, yearRaw, monthRaw, valueRaw] = match;
    const year = Number(yearRaw);
    const month = Number(monthRaw);
    const value = Number(valueRaw);

    if (!Number.isInteger(year) || month < 1 || month > 12) continue;
    if (!Number.isFinite(value) || value <= -99) continue;

    rows.push({
      date: `${year}-${String(month).padStart(2, "0")}-15`,
      season: "",
      year,
      roni: value,
    });
  }

  if (!rows.length) throw new Error("RONI parser returned no observations");
  return rows;
}

function parseOni(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const match = line.match(
      /^\s*(\d{4})\s+([A-Z]{3})\s+([+-]?\d+(?:\.\d+)?)/,
    );
    if (!match) continue;

    const [, yearRaw, monthName, valueRaw] = match;
    const year = Number(yearRaw);
    const month = MONTHS[monthName];
    const value = Number(valueRaw);

    if (!month || !Number.isInteger(year)) continue;
    if (!Number.isFinite(value) || value <= -99) continue;

    rows.push({
      date: `${year}-${String(month).padStart(2, "0")}-15`,
      season: "",
      year,
      oni: value,
    });
  }

  if (!rows.length) throw new Error("ONI parser returned no observations");
  return rows;
}

function parseWeeklyNino(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const match = line.match(
      /^\s*(\d{4})\s+(\d{1,2})\s+([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)/,
    );
    if (!match) continue;

    const [, yearRaw, weekRaw, nino12Raw, nino3Raw, nino34Raw, nino4Raw] = match;
    const year = Number(yearRaw);
    const week = Number(weekRaw);
    const nino12 = Number(nino12Raw);
    const nino3 = Number(nino3Raw);
    const nino34 = Number(nino34Raw);
    const nino4 = Number(nino4Raw);

    if (!Number.isInteger(year) || !Number.isInteger(week)) continue;
    if (week < 1 || week > 53) continue;
    if (![nino12, nino3, nino34, nino4].every(Number.isFinite)) continue;

    rows.push({
      date: `${year}-01-01`,
      week,
      nino12_sst: nino12,
      nino12,
      nino3_sst: nino3,
      nino3,
      nino34_sst: nino34,
      nino34,
      nino4_sst: nino4,
      nino4,
    });
  }

  if (!rows.length) {
    throw new Error("Weekly Niño parser returned no observations");
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

async function githubRequest(env, path, options = {}) {
  return fetch(
    `https://api.github.com/repos/${env.GITHUB_REPOSITORY}/contents/${path}${options.query || ""}`,
    {
      ...options.fetchOptions,
      headers: {
        Authorization: `Bearer ${env.GITHUB_TOKEN}`,
        Accept: "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "enso-data-core",
        ...(options.fetchOptions?.headers || {}),
      },
    },
  );
}

async function publishDataset(env, name, rows, columns, sourceUrl) {
  validateRows(rows, columns);

  const csv = toCsv(rows, columns);
  const digest = await sha256Hex(csv);
  const snapshotId = digest.slice(0, 16);
  const basePath = `data/foundation/${name}`;
  const snapshotPath = `${basePath}/${snapshotId}.csv`;
  const manifestPath = `${basePath}/manifest.jsonl`;

  const snapshotResponse = await githubRequest(env, snapshotPath, {
    fetchOptions: {
      method: "PUT",
      body: JSON.stringify({
        message: `data: publish ${name} snapshot ${snapshotId}`,
        content: btoa(csv),
        branch: env.GIT_BRANCH,
      }),
    },
  });

  if (!snapshotResponse.ok && snapshotResponse.status !== 422) {
    throw new Error(`GitHub snapshot publish failed: ${snapshotResponse.status}`);
  }

  let existingManifest = "";
  let manifestSha;

  const manifestGet = await githubRequest(env, manifestPath, {
    query: `?ref=${encodeURIComponent(env.GIT_BRANCH)}`,
  });

  if (manifestGet.ok) {
    const data = await manifestGet.json();
    manifestSha = data.sha;
    existingManifest = atob(data.content.replace(/\n/g, ""));
  } else if (manifestGet.status !== 404) {
    throw new Error(`GitHub manifest read failed: ${manifestGet.status}`);
  }

  const manifestEntry =
    JSON.stringify({
      dataset: name,
      snapshot_id: snapshotId,
      sha256: digest,
      rows: rows.length,
      retrieved_at: new Date().toISOString(),
      foundation_version: FOUNDATION_VERSION,
      source: "NOAA CPC",
      source_url: sourceUrl,
      start: rows[0].date,
      end: rows[rows.length - 1].date,
    }) + "\n";

  const manifestResponse = await githubRequest(env, manifestPath, {
    fetchOptions: {
      method: "PUT",
      body: JSON.stringify({
        message: `data: update ${name} manifest`,
        content: btoa(existingManifest + manifestEntry),
        branch: env.GIT_BRANCH,
        ...(manifestSha ? { sha: manifestSha } : {}),
      }),
    },
  });

  if (!manifestResponse.ok) {
    throw new Error(`GitHub manifest publish failed: ${manifestResponse.status}`);
  }

  return {
    snapshot_id: snapshotId,
    sha256: digest,
    rows: rows.length,
    start: rows[0].date,
    end: rows[rows.length - 1].date,
  };
}

async function fetchNoaa(url) {
  const response = await fetch(url, {
    headers: { "User-Agent": "enso-data-core" },
  });

  if (!response.ok) {
    throw new Error(`NOAA request failed: ${response.status} ${response.statusText}`);
  }

  const text = await response.text();
  if (!text.trim()) throw new Error("NOAA returned an empty response");
  return text;
}

async function run(env) {
  const results = {};
  const errors = {};

  for (const [name, config] of Object.entries(DATASETS)) {
    try {
      const text = await fetchNoaa(config.url);
      let rows;

      if (name === "roni") rows = parseRoni(text);
      else if (name === "oni") rows = parseOni(text);
      else if (name === "weekly_nino") rows = parseWeeklyNino(text);
      else throw new Error(`Unsupported dataset: ${name}`);

      results[name] = await publishDataset(
        env,
        name,
        rows,
        config.required,
        config.url,
      );
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      errors[name] = message;
      console.error(`Dataset ${name} failed: ${message}`);
    }
  }

  return {
    foundation_version: FOUNDATION_VERSION,
    retrieved_at: new Date().toISOString(),
    results,
    errors,
  };
}

export default {
  async scheduled(controller, env) {
    const result = await run(env);

    console.log(JSON.stringify(result));

    if (Object.keys(result.errors).length > 0) {
      throw new Error(`Foundation run failed: ${JSON.stringify(result.errors)}`);
    }
  },

  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/health") {
      return new Response(
        JSON.stringify({
          status: "ok",
          service: "enso-data-core",
          foundation_version: FOUNDATION_VERSION,
        }),
        {
          headers: { "Content-Type": "application/json" },
        },
      );
    }

    if (url.pathname === "/run") {
      const result = await run(env);
      const status = Object.keys(result.errors).length > 0 ? 500 : 200;

      return new Response(JSON.stringify(result, null, 2), {
        status,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response("ENSO Data Core", {
      status: 200,
      headers: { "Content-Type": "text/plain" },
    });
  },
};
