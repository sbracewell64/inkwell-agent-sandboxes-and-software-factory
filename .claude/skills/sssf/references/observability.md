# Observability Reference

The event schema, the seven SQLite tables, and the polling contract — the one data path is **agents → sqlite → web ui**.

## Two stores, one truth

**Files are the raw record** (`raw_output.jsonl` streams, `envelope.json`, `agent_map.json`); **SQLite (`sssf.db`) is the queryable mirror** the UI reads. `tracer.py` writes both. Losing the db loses nothing that can't be rebuilt from files.

Location comes from `observability.db` in `sssf.config.yaml`, default `adws/adw_data/sssf.db` — inside the **target** repo, gitignored.

## Event schema

`tracer.py` emits these types, every one logged against its `adw_id` **and** `phase_id`:

| Type | Emitted when |
|---|---|
| `phase_start` | a `run.phase(...)` block is entered |
| `agent_start` | a coding agent is spawned or resumed for `ph.call(...)` |
| `thinking` | a complete assistant `message_end` carries one or more thinking blocks; payload includes clipped text, `stop_reason`, and agent |
| `agent_message` | a complete assistant `message_end` carries one or more text blocks; payload includes clipped text, `stop_reason`, and agent |
| `tool_call` | a tool (`read`, `bash`, `edit`, `write`) returns — **one event per real call**, named `bash: ls -la src`, payload `{tool, tool_call_id, args, result_snippet, ok, duration_ms, agent}` |
| `handoff` | an envelope crosses from one agent to the next |
| `gate_pass` | a gate recorded qualifying nonempty positive evidence — payload carries typed `outcome`, `attempt`, `checks`, and `nonempty_required` |
| `gate_fail` | a gate observed at least one failed check — payload retains typed FAIL separately from unavailable evidence |
| `gate_could_not_observe` | required evidence was empty/unavailable, no gates were discovered, or a gate result was untyped; payload preserves closed CNO reason/source |
| `log` | an explicit `ph.log(...)` from the ADW script |
| `agent_end` | the agent's run completes; envelope parsed or not — payload carries `cost`, `usage` (the per-component breakdown), `context_tokens`, `context_window` |
| `phase_end` | the block exits; carries the resolved status |
| `error` | a raise inside a phase block |

`message_update` deltas are deliberately not traced: only complete assistant
messages become `thinking` or `agent_message` events, before the tool call they
narrate. `parent_id` nests spans, so an agent phase expands into its tool-call
spans in the UI.

**Spend is itemised per phase.** `agent_end.usage` carries tokens *and* dollars for each component pi reports — `input`, `output`, `cache_read`, `cache_write` — summed across every send the phase made, so a phase that retried on a bad envelope or a failed gate shows what all its attempts cost, not just the last one. The four components sum to `total_tokens`, and their costs sum to `total_cost`; the visualizer's Cost panel renders them as a table you can add up by eye.

`reasoning_tokens` is the thinking share and is **inside** `output_tokens`, not a fifth component — measured across every session on disk, reasoning never exceeds output and the four components always reconcile to the total. It bills at the output rate, so the panel nests it under output rather than adding it. Runs predating the breakdown have no `usage` key at all; the lump `cost` and the event's own `tokens` still stand, and the UI says so rather than rendering zeroes.

**Context is occupancy, not spend.** `events.tokens` and `sessions.total_tokens` bill every turn, so they only grow — an agent that burned 100k tokens may be sitting in a 15k window. `context_tokens` is how full the window actually was when the agent stopped, which is what the visualizer's per-lane Context bar measures against `context_window`.

It is computed the way pi computes it for its own footer and its auto-compaction trigger (`calculateContextTokens` in the coding agent's `core/compaction/compaction.ts`): take the last *valid* assistant turn — skipping `aborted` and `error` turns — and read `usage.totalTokens`, falling back to `input + output + cacheRead + cacheWrite`. Cache reads count; cached prompt is still prompt. `context_window` is the same `contextWindow` pi reads from `~/.pi/agent/models.json`, so `context_tokens / context_window` is the number pi would show. Both are NULL on rows written before the columns existed, and the lane draws no bar rather than a misleading empty one.

Two caveats worth knowing. Pi adds an *estimate* for any messages trailing the last assistant usage; in a batch (`-p`) run the session ends on that message, so the two agree. And if auto-compaction fires as the very last act of a run, the recorded number is the pre-compaction size — pi itself reports `null` in that window rather than guessing.

**Gates record evidence and a three-valued outcome.** `GateOutcome` in `data_types.py` is the owner of `PASS | FAIL | COULD_NOT_OBSERVE`; it cannot coerce to Boolean. A gate declares `nonempty_required` and returns one `{item, ok, note}` check per observation. A failed check is FAIL. All required observations must be present and positive to PASS. Zero required checks or unavailable evidence is CNO with a closed `cno_reason` and `cno_source`.

Outcome, CNO provenance, requirement, checks, and violations land in `gate_results` and the matching `gate_pass`/`gate_fail`/`gate_could_not_observe` event. Thus PASS can answer *what did you verify* — `{"item": "…/plan.md", "ok": true, "note": "exists, 454B"}` — while CNO remains distinct from a judged defect.

`passed` is compatibility projection only: `1` for PASS, `0` for FAIL, and SQL NULL for CNO. Migration preserves legacy negatives as FAIL and downgrades legacy Boolean green to CNO (`LEGACY_BOOLEAN_ONLY` / `SCHEMA_MIGRATION`); old positives may have been vacuous. A reader opening a schema without typed outcome columns projects CNO (`TRACE_READER`) and never falls back to `passed`. Missing/malformed/unknown typed data and missing checks for a required PASS render CNO.

The gate event payload carries `attempt` too, so the table and event stream retain the same typed result per correction round.

**A `tool_call` is the one event that spans time**, so it fills both `started_at` and `ended_at` on the row — the tool's real start and return. Every other type is a point in time: `started_at` is when it was recorded and `ended_at` stays NULL. Lay tool calls out on a time axis from those columns, never by parsing `payload_json` (`duration_ms` is in the payload too, as pi's own number, but it is a convenience, not the source for layout).

**Streaming is solved by construction.** `agent_pi.py` tails pi's JSONL stdout line by line and the tracer inserts each event into `sssf.db` **while the agent is still working** — never batched at phase end (verified in the first smoke run: tool calls visible mid-run). Everything downstream is a poll → render.

## Tables

```sql
sessions (
  adw_id        TEXT PRIMARY KEY,
  request       TEXT,              -- the engineer's ask
  status        TEXT,              -- running | success | fail
  engineer      TEXT,
  started_at    TEXT, ended_at TEXT,
  total_tokens  INTEGER, total_cost REAL
);

phases (
  phase_id      TEXT PRIMARY KEY,
  adw_id        TEXT REFERENCES sessions,
  seq           INTEGER,
  name TEXT, kind TEXT, owner TEXT, description TEXT,
  status        TEXT DEFAULT 'fail',   -- success must be earned
  attempt       INTEGER DEFAULT 0, retries INTEGER DEFAULT 0,
  error         TEXT,
  started_at    TEXT, ended_at TEXT
);

events (
  event_id      TEXT PRIMARY KEY,
  adw_id        TEXT REFERENCES sessions,
  phase_id      TEXT REFERENCES phases,   -- every event logs against adw + phase
  parent_id     TEXT,                     -- span nesting
  type          TEXT,   -- phase_start | phase_end | agent_start | agent_end
                        -- | thinking | agent_message | tool_call
                        -- | handoff | gate_pass | gate_fail | gate_could_not_observe
                        -- | log | error
  name          TEXT,
  payload_json  TEXT,
  tokens        INTEGER,
  started_at    TEXT, ended_at TEXT   -- ended_at set only on events that span time
);

envelopes (
  envelope_id   TEXT PRIMARY KEY,
  adw_id        TEXT REFERENCES sessions,
  phase_id      TEXT REFERENCES phases,
  agent         TEXT,
  output_type   TEXT,              -- name of the data_types model it parsed against
  payload_json  TEXT,
  valid         INTEGER,
  attempt       INTEGER,
  created_at    TEXT
);

gate_results (
  id            INTEGER PRIMARY KEY,
  adw_id        TEXT REFERENCES sessions,
  phase_id      TEXT REFERENCES phases,
  attempt       INTEGER,
  gate          TEXT,
  passed        INTEGER,            -- compatibility only: 1 PASS, 0 FAIL, NULL CNO
  outcome       TEXT,               -- PASS | FAIL | COULD_NOT_OBSERVE
  cno_reason    TEXT,               -- closed enum; required only for CNO
  cno_source    TEXT,               -- closed enum; required only for CNO
  nonempty_required INTEGER,        -- whether zero checks is CNO
  violations_json TEXT,             -- derived: the failed checks, as "item: note"
  checks_json   TEXT,               -- [{item, ok, note}] — everything the gate looked at
  created_at    TEXT
);

processes (                        -- adw_id → pid, so a stuck run can be stopped
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  adw_id        TEXT REFERENCES sessions,
  kind          TEXT,               -- 'adw' (the workflow process) | 'agent' (a coding-agent child)
  name          TEXT,               -- '' for the adw, the agent name for a child
  pid           INTEGER,
  command       TEXT,               -- what the pid WAS; pids get recycled, so verify before killing
  started_at    TEXT, ended_at TEXT -- ended_at NULL = believed alive
);

agent_sessions (                   -- the queryable mirror of agent_map.json
  adw_id        TEXT REFERENCES sessions,
  agent         TEXT,
  coding_agent  TEXT, model TEXT, color TEXT,   -- color: the config's lane swatch
  session_id    TEXT,
  context_tokens INTEGER,           -- window occupancy after the agent's last turn
  context_window INTEGER,           -- the model's ceiling, from the pi registry
  created_at    TEXT, last_used_at TEXT,
  PRIMARY KEY (adw_id, agent)
);
```

**A hung agent emits nothing**, which is exactly when you need its pid: no events, no tokens, no output to read. `processes` is the only table that can answer "what is this run running, and how do I stop it" — `just procs <adw_id>` lists what is live, `just kill <adw_id>` stops children before the parent, and both verify the recorded `command` still matches the pid before signalling it. A killed run finalizes its own trace: SIGTERM and SIGINT are turned into `SystemExit` in `session.ensure`, so the session lands on `fail` with its process rows closed instead of reading `running` forever.

**Derived, never stored:** phase durations (`ended_at − started_at`), session phase-progress (query `phases` by `adw_id`), lane layout (`kind` + `owner`).

Phase status invariants: `queued` only for manifest-declared phases not yet entered (dashed in the UI); `running` on enter; only a clean exit writes `success` — agent phases additionally need the envelope parsed and gates green; everything else resolves to `fail`.

## WAL pragmas

Open **every** connection — writer and reader — with:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
```

WAL allows readers during writes. Writers are the tracers of running ADW processes; concurrent writers are fine given one small transaction per event plus `busy_timeout`. The visualizer reads on a readonly connection with exactly one exception: archiving a session (`POST /api/sessions/:adw_id/archive`) opens a second connection to set `sessions.archived`. That flag is review triage — it says a human has looked at the run — so it is the reader's state living on the row, and no tracer ever writes or reads it.

## Polling contract

**The UI never receives pushes.** No ingest endpoint, no WebSocket, no backfill or dedup logic.

Live view polls on a rowid cursor every `observability.poll_ms` (default 500):

```sql
SELECT ... FROM events WHERE adw_id = ? AND rowid > ? ORDER BY rowid LIMIT 500;
```

Keep the highest `rowid` returned as the next cursor. History is **the same queries** with filters, lazy-paged as the engineer scrolls or drills in — one mechanism serves both live and past runs, which is why there is no separate replay path.
