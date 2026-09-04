const FOUNDATION_VERSION = "1.1";
const GITHUB_API = "https://api.github.com";
const USER_AGENT = "enso-data-foundation-cloudflare";

const DATASETS = {
  roni: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/RONI.ascii.txt",
    required: ["date", "season", "year", "roni"],
  },
  oni: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    required: ["date", "season", "year", "total", "oni"],
  },
  weekly_nino: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/wksst9120.for",
    required: [
      "date", "nino12_sst", "nino12", "nino3_sst", "nino3",
      "nino34_sst", "nino34", "nino4_sst", "nino4",
      "nino12_ssta", "nino3_ssta", "nino34_ssta", "nino4_ssta",
    ],
  },
  soi: {
    url: "https://www.cpc.ncep.noaa.gov/data/indices/soi",
    required: ["date", "year", "month", "soi"],
  },
};

const SEASONS = new Set(["DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ", "JJA", "JAS", "ASO", "SON", "OND", "NDJ"]);
const CENTRAL_MONTH = { DJF: 1, JFM: 2, FMA: 3, MAM: 4, AMJ: 5, MJJ: 6, JJA: 7, JAS: 8, ASO: 9, SON: 10, OND: 11, NDJ: 12 };
const DATASET_RETRIES = 2;
const RETRY_DELAY_MS = 750;

function pad(n) { return String(n).padStart(2, "0"); }
function seasonDate(season, year) { return `${year}-${pad(CENTRAL_MONTH[season] || 6)}-15T00:00:00`; }

function parseRonI(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    const p = line.trim().split(/\s+/);
    if (p.length < 3 || !SEASONS.has(p[0])) continue;
    const year = Number.parseInt(p[1], 10), roni = Number.parseFloat(p[2]);
    if (!Number.isInteger(year) || !Number.isFinite(roni)) continue;
    rows.push({ season: p[0], year, roni, date: seasonDate(p[0], year) });
  }
  if (!rows.length) throw new Error("No valid RONI records found");
  rows.sort((a, b) => a.date.localeCompare(b.date));
  return rows;
}

function parseOni(text) {
  const rows = [];
  for (const line of text.split(/\r?\n/)) {
    const p = line.trim().split(/\s+/);
    if (p.length < 4 || !SEASONS.has(p[0])) continue;
    const year = Number.parseInt(p[1], 10), total = Number.parseFloat(p[2]), oni = Number.parseFloat(p[3]);
    if (!Number.isInteger(year) || !Number.isFinite(total) || !Number.isFinite(oni)) continue;
    rows.push({ season: p[0], year, total, oni, date: seasonDate(p[0], year) });
  }
  if (!rows.length) throw new Error("No valid ONI records found");
  rows.sort((a, b) => a.date.localeCompare(b.date));
  return rows;
}

function parseWeekly(text) {
  const rows = [];
  const dateRe = /^\s*(\d{1,2}[A-Za-z]{3}\d{4})\s+(.*)$/i;
  const floatRe = /[-+]?\d+\.\d+/g;
  for (const line of text.split(/\r?\n/)) {
    const m = line.match(dateRe);
    if (!m) continue;
    const dt = new Date(`${m[1].slice(0, 2)} ${m[1].slice(2, 5)} ${m[1].slice(5)} UTC`);
    if (Number.isNaN(dt.getTime())) continue;
    const nums = (m[2].match(floatRe) || []).map(Number);
    if (nums.length < 8 || nums.some((v) => !Number.isFinite(v))) continue;
    rows.push({
      date: `${dt.getUTCFullYear()}-${pad(dt.getUTCMonth() + 1)}-${pad(dt.getUTCDate())}T00:00:00`,
      nino12_sst: nums[0], nino12: nums[1], nino3_sst: nums[2], nino3: nums[3],
      nino34_sst: nums[4], nino34: nums[5], nino4_sst: nums[6], nino4: nums[7],
      nino12_ssta: nums[1], nino3_ssta: nums[3], nino34_ssta: nums[5], nino4_ssta: nums[7],
    });
  }
  if (!rows.length) throw new Error("No valid weekly Niño records found");
  rows.sort((a, b) => a.date.localeCompare(b.date));
  return rows;
}

function parseSoi(text) {
  const rows = [];
  const lines = text.split(/\r?\n/);
  const headerIndex = lines.findIndex((line) => /^\s*YEAR\s+JAN\s+FEB/.test(line));
  if (headerIndex < 0) throw new Error("SOI header not found");
  for (const line of lines.slice(headerIndex + 1)) {
    const m = line.match(/^\s*(\d{4})(.*)$/);
    if (!m) continue;
    const year = Number.parseInt(m[1], 10);
    const values = (m[2].match(/[-+]?\d+(?:\.\d+)?/g) || []).map(Number);
    if (!Number.isInteger(year) || values.length < 12) continue;
    for (let month = 1; month <= 12; month += 1) {
      const soi = values[month - 1];
      if (!Number.isFinite(soi) || soi <= -999) continue;
      rows.push({ year, month, soi, date: `${year}-${pad(month)}-15T00:00:00` });
    }
  }
  if (!rows.length) throw new Error("No valid SOI records found");
  rows.sort((a, b) => a.date.localeCompare(b.date));
  return rows;
}

function escapeCsv(value) {
  const s = value instanceof Date ? value.toISOString() : String(value ?? "");
  return /[",\n]/.test(s) ? `"${s.replaceAll('"', '""')}"` : s;
}

function csv(rows, columns) {
  return [columns.join(","), ...rows.map((r) => columns.map((c) => escapeCsv(r[c])).join(","))].join("\n") + "\n";
}

function canonicalize(rows, required) {
  const columns = [...required];
  const normalized = rows.map((r) => Object.fromEntries(columns.map((c) => [c, r[c]])));
  return { rows: normalized, columns };
}

function validate(rows, required) {
  const missing = required.filter((c) => !rows.every((r) => Object.hasOwn(r, c)));
  const dates = rows.map((r) => r.date);
  const duplicateDates = dates.length - new Set(dates).size;
  const dateMonotonic = dates.every((d, i) => i === 0 || dates[i - 1] <= d);
  const numeric = required.filter((c) => !["date", "season", "year"].includes(c));
  const nonNumeric = numeric.filter((c) => rows.some((r) => !Number.isFinite(Number(r[c]))));
  return {
    valid: rows.length > 0 && !missing.length && duplicateDates === 0 && dateMonotonic && !nonNumeric.length,
    rows: rows.length, columns: required, duplicate_rows: 0, duplicate_dates: duplicateDates,
    missing_required: missing, non_numeric_values: nonNumeric, date_monotonic: dateMonotonic,
    message: missing.length ? "missing required columns" : nonNumeric.length ? "non-numeric values" : duplicateDates ? "duplicate dates" : !dateMonotonic ? "invalid or non-monotonic dates" : "OK",
  };
}

async function sha256Hex(text) {
  const bytes = new TextEncoder().encode(text);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 16);
}

function b64(text) { return btoa(unescape(encodeURIComponent(text))); }
function headers(token) { return { Authorization: `Bearer ${token}`, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28", "User-Agent": USER_AGENT }; }

async function githubFile(env, path) {
  const url = `${GITHUB_API}/repos/${env.GITHUB_REPOSITORY}/contents/${path}?ref=${encodeURIComponent(env.GIT_BRANCH)}`;
  const res = await fetch(url, { headers: headers(env.GITHUB_TOKEN) });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`GitHub GET ${path}: ${res.status} ${await res.text()}`);
  return res.json();
}

async function putGithubFile(env, path, content, message, sha = undefined) {
  const url = `${GITHUB_API}/repos/${env.GITHUB_REPOSITORY}/contents/${path}`;
  const body = { message, content: b64(content), branch: env.GIT_BRANCH };
  if (sha) body.sha = sha;
  const res = await fetch(url, { method: "PUT", headers: { ...headers(env.GITHUB_TOKEN), "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`GitHub PUT ${path}: ${res.status} ${await res.text()}`);
  return res.json();
}

async function publishDataset(env, dataset, rows, required, sourceUrl, datasetLabel) {
  const { rows: canonical, columns } = canonicalize(rows, required);
  const validation = validate(canonical, required);
  if (!validation.valid) throw new Error(`${dataset}: validation failed: ${validation.message}`);
  const content = csv(canonical, columns);
  const snapshotId = await sha256Hex(content);
  const base = `data/foundation/${dataset}`;
  const csvPath = `${base}/${snapshotId}.csv`;
  const manifestPath = `${base}/manifest.jsonl`;
  const existingCsv = await githubFile(env, csvPath);
  if (!existingCsv) await putGithubFile(env, csvPath, content, `data: add ${dataset} NOAA snapshot ${snapshotId}`);

  const existingManifest = await githubFile(env, manifestPath);
  let lines = [];
  let manifestSha;
  if (existingManifest) {
    manifestSha = existingManifest.sha;
    const decoded = decodeURIComponent(escape(atob(existingManifest.content.replace(/\n/g, ""))));
    lines = decoded.split(/\r?\n/).filter(Boolean);
  }
  const known = new Set(lines.map((line) => { try { return JSON.parse(line).snapshot_id; } catch { return null; } }));
  if (!known.has(snapshotId)) {
    const start = canonical[0]?.date ?? null;
    const end = canonical.at(-1)?.date ?? null;
    const metadata = {
      dataset: datasetLabel, source: "NOAA CPC", source_url: sourceUrl,
      retrieved_at: new Date().toISOString(), snapshot_id: snapshotId,
      rows: canonical.length, start, end, validation,
    };
    lines.push(JSON.stringify(metadata));
    await putGithubFile(env, manifestPath, lines.join("\n") + "\n", `data: update ${dataset} foundation manifest`, manifestSha);
  }
  return { dataset, snapshotId, rows: canonical.length, created: !existingCsv };
}

function sleep(ms) { return new Promise((resolve) => setTimeout(resolve, ms)); }

async function fetchDatasetWithRetry(name, spec) {
  let lastError;
  for (let attempt = 0; attempt <= DATASET_RETRIES; attempt += 1) {
    try {
      const res = await fetch(spec.url, { headers: { "User-Agent": USER_AGENT } });
      if (!res.ok) throw new Error(`NOAA ${name}: ${res.status}`);
      return await res.text();
    } catch (error) {
      lastError = error;
      if (attempt < DATASET_RETRIES) await sleep(RETRY_DELAY_MS * (attempt + 1));
    }
  }
  throw lastError;
}

async function run(env) {
  if (!env.GITHUB_TOKEN) throw new Error("GITHUB_TOKEN secret is required");
  const results = [];
  const errors = [];
  for (const [name, spec] of Object.entries(DATASETS)) {
    try {
      const text = await fetchDatasetWithRetry(name, spec);
      const rows = name === "roni" ? parseRonI(text) : name === "oni" ? parseOni(text) : name === "weekly_nino" ? parseWeekly(text) : parseSoi(text);
      const label = name === "roni"
        ? "Relative Oceanic Niño Index (RONI)"
        : name === "oni"
          ? "Oceanic Niño Index (ONI)"
          : name === "weekly_nino"
            ? "Weekly Niño region SSTA (OISST.v2.1, 1991–2020)"
            : "Southern Oscillation Index (SOI)";
      results.push(await publishDataset(env, name, rows, spec.required, spec.url, label));
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      errors.push({ dataset: name, error: message });
      console.error(`Dataset ${name} failed: ${message}`);
    }
  }
  console.log(JSON.stringify({ foundation_version: FOUNDATION_VERSION, results, errors }));
}

export default {
  async scheduled(controller, env, ctx) {
    ctx.waitUntil(run(env));
  },
  async fetch(request, env, ctx) {
    if (new URL(request.url).pathname !== "/health") return new Response("Not found", { status: 404 });
    return new Response(JSON.stringify({ service: "enso-data-foundation", status: "ok" }), { headers: { "content-type": "application/json" } });
  },
};
