const FOUNDATION_VERSION = "1.2";

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

const SEASONS = new Set([
  "DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
  "JJA", "JAS", "ASO", "SON", "OND", "NDJ",
]);

const SEASON_CENTRAL_MONTH = {
  DJF: 1,
  JFM: 2,
  FMA: 3,
  MAM: 4,
  AMJ: 5,
  MJJ: 6,
  JJA: 7,
  JAS: 8,
  ASO: 9,
  SON: 10,
  OND: 11,
  NDJ: 12,
};

const WEEKLY_DATE_RE = /^\s*(\d{1,2}[A-Za-z]{3}\d{4})\s+(.*)$/i;
const FLOAT_RE = /[-+]?\d+\.\d+/g;

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

function seasonDate(season, year) {
  const month = SEASON_CENTRAL_MONTH[season];
  return `${year}-${String(month).padStart(2, "0")}-15`;
}

function parseRoni(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const parts = line.trim().split(/\s+/);
    if (parts.length < 3) continue;

    const [season, yearRaw, valueRaw] = parts;
    if (!SEASONS.has(season)) continue;

    const year = Number(yearRaw);
    const value = Number(valueRaw);
    if (!Number.isInteger(year)) continue;
    if (!Number.isFinite(value) || value <= -99) continue;

    rows.push({
      date: seasonDate(season, year),
      season,
      year,
      roni: value,
    });
  }

  if (!rows.length) throw new Error("RONI parser returned no observations");
  return rows.sort((a, b) => a.date.localeCompare(b.date));
}

function parseOni(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const parts = line.trim().split(/\s+/);
    if (parts.length < 4) continue;

    const [season, yearRaw, totalRaw, anomalyRaw] = parts;
    if (!SEASONS.has(season)) continue;

    const year = Number(yearRaw);
    const total = Number(totalRaw);
    const anomaly = Number(anomalyRaw);
    if (!Number.isInteger(year)) continue;
    if (!Number.isFinite(total) || !Number.isFinite(anomaly)) continue;
    if (anomaly <= -99) continue;

    rows.push({
      date: seasonDate(season, year),
      season,
      year,
      total,
      oni: anomaly,
    });
  }

  if (!rows.length) throw new Error("ONI parser returned no observations");
  return rows.sort((a, b) => a.date.localeCompare(b.date));
}

function parseWeeklyDate(dateRaw) {
  const match = dateRaw.match(/^(\d{1,2})([A-Za-z]{3})(\d{4})$/i);
  if (!match) return null;

  const [, dayRaw, monthRaw, yearRaw] = match;
  const months = {
    JAN: 1, FEB: 2, MAR: 3, APR: 4, MAY: 5, JUN: 6,
    JUL: 7, AUG: 8, SEP: 9, OCT: 10, NOV: 11, DEC: 12,
  };
  const month = months[monthRaw.toUpperCase()];
  const day = Number(dayRaw);
  const year = Number(yearRaw);

  if (!month || !Number.isInteger(day) || !Number.isInteger(year)) return null;
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

function parseWeeklyNino(text) {
  const rows = [];

  for (const line of text.split(/\r?\n/)) {
    const match = line.match(WEEKLY_DATE_RE);
    if (!match) continue;

    const date = parseWeeklyDate(match[1]);
    if (!date) continue;

    const nums = [...(match[2].matchAll(FLOAT_RE))].map((m) => Number(m[0]));
    if (nums.length < 8) continue;

    rows.push({
      date,
      nino12_sst: nums[0],
      nino12: nums[1],
      nino3_sst: nums[2],
      nino3: nums[3],
      nino34_sst: nums[4],
      nino34: nums[5],
      nino4_sst: nums[6],
      nino4: nums[7],
    });
  }

  if (!rows.length) throw new Error("Weekly Niño parser returned no observations");
  return rows.sort((a, b) => a.date.localeCompare(b.date));
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

  const seen = new Set();
  for (const row of rows) {
    const key = row.date;
    if (seen.has(key)) throw new Error(`Duplicate date: ${key}`);
    seen.add(key);
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
    const detail = await snapshotResponse.text();
    throw new Error(`GitHub snapshot publish failed: ${snapshotResponse.status} ${detail}`);
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
    const detail = await manifestGet.text();
    throw new Error(`GitHub manifest read failed: ${manifestGet.status} ${detail}`);
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
    const detail = await manifestResponse.text();
    throw new Error(`GitHub manifest publish failed: ${manifestResponse.status} ${detail}`);
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
        { headers: { "Content-Type": "application/json" } },
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
