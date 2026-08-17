/**
 * HD-13: actually RUN the visualizer's read surface and record what was observed.
 *
 * The stdlib validator cannot execute TypeScript, so on its own it can only read
 * the construction site. This exercise runs the real `SssfDb` against a real
 * fixture database and proves two things by property, not by inspection:
 *
 *   1. every read method leaves the database byte-identical;
 *   2. a mutation attempted through the read connection those methods use FAILS,
 *      and still leaves the database byte-identical.
 *
 * A run that only proved the surface executes would prove nothing about
 * read-only-ness, so the refused mutation is mandatory: if it succeeds, this
 * exercise records observed-bad rather than omitting the attempt.
 *
 * It records the exact SHA-256 of the TypeScript it ran against. The stdlib CI
 * check compares those digests with the current bytes, so "these bytes were
 * really exercised" stays true instead of decaying into a claim about source
 * that has since moved. Comparing digests needs no Bun; executing does.
 *
 *   bun docs/validation/exercise_visualizer_read_surface.ts \
 *     --db <fixture.db> --adw-id <id> --out <evidence.json>
 */
import { Database } from "bun:sqlite";
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";
import { SssfDb } from "../../.claude/skills/sssf/apps/visualizer/server/db.ts";

const EXERCISE = "hd13.visualizer-read-surface.v1";
const REPO_ROOT = resolve(import.meta.dir, "..", "..");

/** The TypeScript this exercise binds itself to. */
const SOURCES = [
  ".claude/skills/sssf/apps/visualizer/server/db.ts",
  ".claude/skills/sssf/apps/visualizer/server/index.ts",
];

function arg(name: string, fallback?: string): string {
  const index = Bun.argv.indexOf(`--${name}`);
  const value = index === -1 ? undefined : Bun.argv[index + 1];
  if (value === undefined) {
    if (fallback !== undefined) return fallback;
    throw new Error(`missing required --${name}`);
  }
  return value;
}

function digest(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

/** Canonical bytes, matching the manifest core: sorted keys, one final LF. */
function canonicalJson(value: unknown): string {
  const sort = (input: unknown): unknown => {
    if (Array.isArray(input)) return input.map(sort);
    if (input && typeof input === "object") {
      return Object.fromEntries(
        Object.keys(input as Record<string, unknown>)
          .sort()
          .map((key) => [key, sort((input as Record<string, unknown>)[key])]),
      );
    }
    return input;
  };
  return `${JSON.stringify(sort(value))}\n`;
}

const dbPath = resolve(arg("db"));
const adwId = arg("adw-id");
const outPath = resolve(arg("out"));

const sources: Record<string, string> = {};
for (const relative of SOURCES) sources[relative] = digest(resolve(REPO_ROOT, relative));

const before = digest(dbPath);

// Every read the server can reach. A method added to db.ts and not listed here
// is caught by the stdlib check, which requires this list to cover the reader's
// public read methods.
const readMethods = [
  "sessions",
  "session",
  "phases",
  "agentSessions",
  "sessionDetail",
  "usage",
  "events",
  "envelopes",
  "gates",
  "sessionCount",
];

const db = new SssfDb(dbPath);
const rowCounts: Record<string, number> = {};
try {
  rowCounts.sessions = db.sessions(200).length;
  rowCounts.session = db.session(adwId) ? 1 : 0;
  rowCounts.phases = db.phases(adwId).length;
  rowCounts.agentSessions = db.agentSessions(adwId).length;
  rowCounts.sessionDetail = db.sessionDetail(adwId) ? 1 : 0;
  const usage = db.usage(adwId);
  rowCounts.usage = usage.read + usage.written;
  rowCounts.events = db.events(adwId, 0, 500).events.length;
  rowCounts.envelopes = db.envelopes(adwId).length;
  rowCounts.gates = db.gates(adwId).length;
  rowCounts.sessionCount = db.sessionCount();

  const afterReads = digest(dbPath);

  // The mutation goes through the very connection the read methods above used.
  // `readonly` is a TypeScript modifier and is erased at runtime, so this reaches
  // the real read handle rather than a stand-in opened for the occasion.
  const readConnection = (db as unknown as { db: Database }).db;
  let mutationRefused = false;
  let mutationError = "";
  try {
    readConnection.exec(`UPDATE sessions SET status = 'tampered' WHERE adw_id = '${adwId}'`);
  } catch (error) {
    mutationRefused = true;
    mutationError = (error as Error).message;
  }

  const afterMutation = digest(dbPath);
  const unchanged = before === afterReads && before === afterMutation;

  const record = {
    schema_version: 1,
    exercise: EXERCISE,
    observation: mutationRefused && unchanged ? "observed-good" : "observed-bad",
    runtime: { name: "bun", version: Bun.version },
    observed_at: new Date().toISOString().replace(/\.\d{3}Z$/, "Z"),
    sources,
    fixture: {
      digest_before: before,
      digest_after_reads: afterReads,
      digest_after_mutation_attempt: afterMutation,
      unchanged,
    },
    reads: { methods: readMethods, row_counts: rowCounts },
    mutation: {
      attempted: true,
      statement: "UPDATE sessions SET status = 'tampered' WHERE adw_id = ?",
      refused: mutationRefused,
      error: mutationError,
    },
  };

  writeFileSync(outPath, canonicalJson(record), "utf-8");
  console.log(`${EXERCISE}: ${record.observation}`);
  console.log(`  bun ${Bun.version}`);
  for (const [relative, sha] of Object.entries(sources)) console.log(`  ${sha}  ${relative}`);
  console.log(`  reads left the database unchanged: ${before === afterReads}`);
  console.log(`  mutation through the read connection refused: ${mutationRefused}`);
  if (mutationError) console.log(`  refusal: ${mutationError}`);
  console.log(`  evidence: ${outPath}`);
  process.exit(record.observation === "observed-good" ? 0 : 1);
} finally {
  db.close();
}
