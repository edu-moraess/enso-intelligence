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
    required: ["date", "week", "nino12_sst", "nino12", "nino3_sst", "nino3", "nino34_sst", "nino34", "nino4_sst", "nino4"],
  },
  soi: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/soi",
    required: ["date", "year", "month", "soi"],
  },
};

const MONTHS = { JAN: 1, FEB: 2, MAR: 3, APR: 4, MAY: 5, JUN: 6, JUL: 7, AUG: 8, SEP: 9, OCT: 10, NOV: 11, DEC: 12 };

async function sha256Hex(input) {
  const buffer = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return [...new Uint8Array(buffer)].map(b => b.toString(16).padStart(2, "0")).join("");
}

function csvEscape(value) {
  const text = String(value ?? "");
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

function toCsv(rows, columns) {
  return [columns.join(","), ...rows.map(row => columns.map(column => csvEscape(row[column])).join(","))].join("\n") + "\n";
}

function parseRoni(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/^\s*(\d{4})\s+(\d{1,2})\s+([+-]?\d+(?:\.\d+)?)/);
    if (!match) continue;
    const [, year, month, value] = match;
    const monthNumber = Number(month);
    rows.push({ date: `${year}-${String(monthNumber).padStart(2, "0")}-15`, season: "", year: Number(year), roni: Number(value) });
  }
  if (!rows.length) throw new Error("RONI parser returned no observations");
  return rows;
}

function parseOni(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/^\s*(\d{4})\s+([A-Z]{3})\s+([+-]?\d+(?:\.\d+)?)/);
    if (!match) continue;
    const [, year, monthName, value] = match;
    const month = MONTHS[monthName];
    if (!month) continue;
    rows.push({ date: `${year}-${String(month).padStart(2, "0")}-15`, season: "", year: Number(year), oni: Number(value) });
  }
  if (!rows.length) throw new Error("ONI parser returned no observations");
  return rows;
}

function parseWeeklyNino(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(/^\s*(\d{4})\s+(\d{1,2})\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)\s+(\d+(?:\.\d+)?)/);
    if (!match) continue;
    const [, year, week, nino12, nino3, nino34, nino4] = match;
    rows.push({ date: `${year}-01-01`, week: Number(week), nino12_sst: Number(nino12), nino12: Number(nino12), nino3_sst: Number(nino3), nino3: Number(nino3), nino34_sst: Number(nino34), nino34: Number(nino34), nino4_sst: Number(nino4), nino4: Number(nino4) });
  }
  if (!rows.length) throw new Error("Weekly Niño parser returned no observations");
  return rows;
}

function parseSoi(text) {
  const lines = text.split(/\r?\n/);
  const headerIndex = lines.findIndex(line => /^\s*YEAR\s+JAN\s+FEB/i.test(line));
  if (headerIndex === -1) throw new Error("SOI header not found");
  const rows = [];
  const numberPattern = /[-+]?\d+(?:\.\d+)?/g;

  for (const line of lines.slice(headerIndex + 1)) {
    const match = line.match(/^\s*(\d{4})(.*)$/);
    if (!match) continue;
    const year = Number(match[1]);
    const values = match[2].match(numberPattern) || [];
    if (values.length < 12) continue;
    values.slice(0, 12).forEach((raw, index) => {
      const value = Number(raw);
      if (!Number.isFinite(value) || value <= -999) return;
      rows.push({ date: `${year}-${String(index + 1).padStart(2, "0")}-15`, year, month: index + 1, soi: value });
    });
  }
  if (!rows.length) throw new Error("SOI parser returned no observations");
  return rows;
}

function validateRows(rows, required) {
  if (!Array.isArray(rows) || rows.length === 0) throw new Error("Dataset contains no rows");
  for (const column of required) if (!(column in rows[0])) throw new Error(`Missing required column: ${column}`);
}

function buildValidation(rows, required) {
  const missing = required.filter(column => rows.some(row => row[column] === undefined || row[column] === null || row[column] === ""));
  return { required_columns: required, missing_columns: missing, valid: missing.length === 0 && rows.length > 0 };
}

async function githubJson(env, path, options = {}) {
  const response = await fetch(`https://api.github.com/repos/${env.GITHUB_REPOSITORY}/contents/${path}${options.query || ""}`, {
    ...options.fetchOptions,
    headers: { Authorization: `Bearer ${env.GITHUB_TOKEN}`, "Content-Type": "application/json", "User-Agent": "enso-data-foundation", ...(options.fetchOptions?.headers || {}) },
  });
  return response;
}

async function publishDataset(env, name, rows, columns, sourceUrl) {
  validateRows(rows, columns);
  const validation = buildValidation(rows, columns);
  if (!validation.valid) throw new Error(`Dataset validation failed: ${validation.missing_columns.join(", ")}`);

  const csv = toCsv(rows, columns);
  const digest = await sha256Hex(csv);
  const snapshotId = digest.slice(0, 16);
  const basePath = `data/foundation/${name}`;
  const snapshotPath = `${basePath}/${snapshotId}.csv`;
  const manifestPath = `${basePath}/manifest.jsonl`;

  const snapshotResponse = await githubJson(env, snapshotPath, {
    fetchOptions: { method: "PUT", body: JSON.stringify({ message: `data: publish ${name} snapshot ${snapshotId}`, content: btoa(csv), branch: env.GIT_BRANCH }) },
  });
  if (!snapshotResponse.ok && snapshotResponse.status !== 422) throw new Error(`GitHub snapshot publish failed: ${snapshotResponse.status}`);

  let existingManifest = "";
  let manifestSha;
  const manifestGet = await githubJson(env, manifestPath, { query: `?ref=${encodeURIComponent(env.GIT_BRANCH)}` });
  if (manifestGet.ok) {
    const data = await manifestGet.json();
    manifestSha = data.sha;
    existingManifest = atob(data.content.replace(/\n/g, ""));
  } else if (manifestGet.status !== 404) {
    throw new Error(`GitHub manifest read failed: ${manifestGet.status}`);
  }

  const manifestEntry = JSON.stringify({
    dataset: name,
    snapshot_id: snapshotId,
    sha256: digest,
    rows: rows.length,
    retrieved_at: new Date().toISOString(),
    foundation_version: FOUNDATION_VERSION,
    source: "NOAA CPC",
    source_url: sourceUrl,
    validation,
    start: rows[0].date,
    end: rows[rows.length - 1].date,
  }) + "\n";

  const manifestResponse = await githubJson(env, manifestPath, {
    fetchOptions: { method: "PUT", body: JSON.stringify({ message: `data: update ${name} manifest`, content: btoa(existingManifest + manifestEntry), branch: env.GIT_BRANCH, ...(manifestSha ? { sha: manifestSha } : {}) }) },
  });
  if (!manifestResponse.ok) throw new Error(`GitHub manifest publish failed: ${manifestResponse.status}`);

  return { snapshot_id: snapshotId, sha256: digest, rows: rows.length, start: rows[0].date, end: rows[rows.length - 1].date };
}

async function fetchNoaa(url) {
  const response = await fetch(url, { headers: { "User-Agent": "enso-data-foundation" } });
  if (!response.ok) throw new Error(`NOAA request failed: ${response.status} ${response.statusText}`);
  return response.text();
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
      else if (name === "soi") rows = parseSoi(text);
      results[name] = await publishDataset(env, name, rows, config.required, config.url);
    } catch (error) {
      errors[name] = error instanceof Error ? error.message : String(error);
      console.error(`Dataset ${name} failed: ${errors[name]}`);
    }
  }
  console.log(JSON.stringify({ foundation_version: FOUNDATION_VERSION, retrieved_at: new Date().toISOString(), results, errors }));
  return { results, errors };
}

export default {
  async scheduled(controller, env) {
    await run(env);
  },
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === "/health") return new Response(JSON.stringify({ status: "ok", foundation_version: FOUNDATION_VERSION }), { headers: { "Content-Type": "application/json" } });
    if (url.pathname === "/run") {
      const result = await run(env);
      const status = Object.keys(result.errors).length ? 500 : 200;
      return new Response(JSON.stringify(result), { status, headers: { "Content-Type": "application/json" } });
    }
    return new Response("ENSO Data Foundation", { status: 200 });
  },
};
