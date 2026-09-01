# Baseline — SSSF-LOCAL-B0

**Status:** FROZEN — PROVEN WITH RECORDED LIMITATIONS
**Date proven:** 2026-08-13
**Purpose:** Establish a reproducible reference point before architectural augmentation.

## Post-baseline lifecycle status

The B0 proof remains frozen; later `main` changes do not retroactively enlarge it.
SBX-1 is a **landed implementation** of the provider-neutral contract and
deterministic fake controls. SBX-1 is not activated, not accepted, not
certified, and not real-provider-proven; it does not unlock SBX-2. Real
provider/Docker custody, supported Windows-host execution, and the missing
historical landing-governance evidence remain CNO or unmet.

BOUND-1 is a **landed implementation** of the repository-wide boundedness audit
and its continuous enforcement: `docs/reference/BOUNDEDNESS_REGISTRY.json` bound
against exact main `8aadd50461b184cede949f21ecf426146f2915a0`, tree
`f1b779f73bea2b33810e5663e9dc2f3b82ea9299`, with
`docs/validation/check_boundedness.py` registered in required CI. BOUND-1 is not
accepted, not certified, and not PROVEN; it does not unlock SBX-2 and does not
change the Docker → baseline → Wayfinder → DSH sequence. Assignment-distinct
semantic review, exact-head CI on the landed bytes, LandingAuthorization, and
Windows-host observation of the changed owners remain CNO or unmet.

## Source baseline

- Repository: `disler/inkwell-agent-sandboxes-and-software-factory`
- Upstream source SHA observed in the successful sandbox: `92f1701810993b8303562265ba04c727468fe070`
- Local checkout root: `E:\SSSF`

The proof run cloned the upstream source into the sandbox. The proof's app modification is evidence of factory operation; it is **not automatically part of the core baseline**.

## Host installation proven

The following host-side preflight passed:

- Git available.
- Bun `1.3.14`.
- uv `0.12.3`.
- just `1.58.0`.
- Git-for-Windows Bash available.
- `cygpath` available after adding Git `usr\bin` to `PATH`.
- exe.dev SSH authentication operational with a dedicated Ed25519 key.
- `OPENROUTER_PROVISIONING_KEY` recognized.
- SSSF helper/provisioner/model-template/ADW preflight passed.
- `just sbx manage doctor` ended `sbx doctor: OK`.
- `just inkwell test` passed 30/30 tests.

## Windows compatibility overlay

The upstream checkout required narrow host compatibility changes before the stock lifecycle could complete on this Windows Command Prompt environment:

1. `just/sandbox/lifecycle/create.just`
   - strip trailing `\r` from parsed `VM_NAME` and `HTTPS_URL`;
   - reason: Windows Python output was read by Bash with CRLF contamination, producing a VM name ending in `\r`.

2. `just/sandbox/lifecycle/teardown.just`
   - change `mktemp -t "sbx-$RUN_ID"` to `mktemp -t "sbx-$RUN_ID.XXXXXX"`;
   - reason: Git/MSYS `mktemp` requires an X template.

3. Windows SSH config
   - `Host exe.dev *.exe.xyz`
   - dedicated identity file
   - `IdentitiesOnly yes`
   - `StrictHostKeyChecking accept-new`
   - reason: non-interactive SSSF readiness probes must not stop on first-seen VM host-key prompts.

4. Command Prompt PATH
   - include `C:\Program Files\Git\bin`
   - include `C:\Program Files\Git\usr\bin`
   - reason: `sh` and `cygpath` are required by the `just` recipes.

These are part of the **local baseline environment contract** until upstream or a later portability increment removes them.

## Successful sandbox lifecycle proof

Sandbox run:

`baseline-proof-20260813-d38790`

Observed successful path:

`create -> fill -> setup -> observe`

The VM was created, the repo cloned, a per-run OpenRouter key injected, guest tooling provisioned, the trace DB initialized, the health gate completed, Inkwell started on port 4501, and the observability service started on port 4600.

## Successful free-inference ADW proof

A separate free roster was created inside the proof sandbox.

Planner and builder:

`openrouter/cohere/north-mini-code:free`

Successful ADW:

- `adw_id`: `5573998b`
- phases: `5/5`
- status: `success`
- test command: `bun test apps/inkwell/server.test.ts`
- test result: pass
- commit: `042dfb9`
- reported inference cost: `$0.0000`
- reported tokens: `420,217`

The run proved:

- typed planner output,
- filesystem artifact gates,
- enforced planner write boundary,
- rollback of an unauthorized planner app edit,
- same-session builder retry after malformed `BuildOutput`,
- builder implementation,
- deterministic test execution,
- commit only after the test passed.

## Proof change

The proof task asked for a small `Baseline proof` footer label.

Commit `042dfb9` contained:

- `adws/adw_sssf_config/sssf.free.config.yaml`
- `apps/inkwell/public/index.html`
- `specs/5573998b_inkwell-footer-label.md`

The public endpoint served the committed HTML containing the label and served the current stylesheet.

## Recorded limitations / unresolved items

These are **not silently treated as solved**:

1. The setup gate reported PASS even while model probes printed insufficient-credit failures. The later real ADW proved free inference separately, but the gate semantics are suspect and should be repaired in a future increment.
2. `just obs sessions` failed on the Windows host because `sqlite3` was not installed.
3. The proof marker was present in the public HTML but was not visually apparent in the browser. This is an application-presentation discrepancy, not a failure of the factory execution chain. It remains unclosed evidence.
4. exe.dev is a commercial sandbox service. The current access is temporary; replacing it with a free/local sandbox is a planned post-baseline increment.
5. Free OpenRouter model availability is volatile. A free roster is operational configuration, not a permanent architectural guarantee.
6. The current proof sandbox must be harvested and torn down before the baseline is considered fully archived.

## Baseline acceptance rule

`SSSF-LOCAL-B0` is frozen only after the freeze procedure in `FREEZE_PROCEDURE.md` is completed and its immutable Git refs are recorded here.

## Freeze record

- Baseline tag: `sssf-local-b0`
- Proof tag: `sssf-proof-b0`
- Upstream source: `92f1701810993b8303562265ba04c727468fe070`
- End-to-end proof commit: `042dfb9d34a14fe5952538fedddbd136b334947e`
- End-to-end proof ADW: `5573998b`
- Proof sandbox: `baseline-proof-20260813-d38790`
- Successful proof sandbox was harvested, its runtime key revoked, VM destroyed, and run record closed before baseline publication.
