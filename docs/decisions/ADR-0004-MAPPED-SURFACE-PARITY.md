# ADR-0004 — Mapped-Surface Parity Between Template and Live Bytes

**Status:** Accepted
**Date:** 2026-08-16
**Ruling:** browser-sol `5308853615` (PROCEED_WITH_CONDITIONS)

## Context

SSSF ships the same ADW substrate twice: the live tree under `adws/`, and the
installable skill template under `.claude/skills/sssf/templates/` that
`install.py` stamps into any target repository. Nothing owned the relationship
between them.

Two facts made that gap worse than an ordinary missing check.

**The surfaces are not a subtree mirror.** `install.py` stamps template paths to
*different* live paths — `templates/prompt_engineering/` to
`adws/adw_data/prompt_engineering/`, `templates/sssf.config.yaml` to
`adws/adw_sssf_config/sssf.config.yaml`, `templates/env.sample` to `.env.sample`.
A relative-path comparison of the two roots is therefore not a parity model at
all: it reports correctly-mapped trees as absent. An investigation using
`diff -rq` concluded that seventeen files were missing from the template; the
files were present, mapped elsewhere, and the comparison model was wrong.

**Some divergence is correct.** `adw_modules/quality.py` ships in the template as
placeholder blocks that exit 0 and announce they are fake, because a stamped repo
cannot guess its own test runner and a wrong-but-plausible command that silently
passes is worse than one that says so. The roster config, `.env.sample` and the
justfile are stamped once and then owned by the target repo. Flattening the two
surfaces would destroy all of this while looking like a tidy-up.

So the naive repair (copy one surface onto the other) and the naive detector
(subtree diff) are both wrong, and a real defect hid between them: the
preserve/restore permissions mechanism, its assistant-message tracing, and the
prompt notice describing them landed live-only, and the dormant
`subprocess_supervisor.py` / `pi_json_adapter.py` pair was never stamped at all.
`check_adw_synchronization.py` printed `PASS` throughout, correctly — it owns
contract shape, not content.

## Decision

**One repository-owned, machine-readable contract is authoritative for the
relationship between installable template bytes and live bytes:**
`docs/validation/mapped_surface_contract.json`.

1. **The mapping is transcribed, not inferred.** The contract records the
   `stamp()` calls in `install.py`'s `main()` as the source of truth, including
   every non-isomorphic pair. Prose describes the mapping; it does not define it.

2. **Every governed path resolves to exactly one typed relation:**
   `EXACT_MIRROR`, `CONTRACT_ONLY`, `TEMPLATE_SCAFFOLD`, `USER_OWNED`, or
   `LIVE_ONLY`. Intentional divergence carries an owner, a rationale, and
   evidence. An added, removed, or divergent governed path with no declared
   relation is a non-pass — never a silent accept.

3. **A relation that permits body divergence must name the property it still
   guarantees.** `TEMPLATE_SCAFFOLD` on `quality.py` names the exact exports
   (`run_inkwell_tests`, `run_inkwell_quality`, `as_envelope`) and the exact
   verifier symbol that enforces them. A filename or a validator's name is not
   proof, so an escape hatch that names no falsifiable property is refused.

4. **Parity gets its own verifier, separate from contract shape.**
   `check_mapped_surface_parity.py` owns the mapped content relationship;
   `check_adw_synchronization.py` (HD-02) is preserved unchanged and continues to
   own per-surface contract shape. They are not merged. Their names sounded
   interchangeable and were not, which is precisely what let the gap persist, so
   the fix is a clearer boundary rather than a bigger validator.

5. **The verifier proves it still works on every run.** Watched-red calibration
   is not behind a flag: each invocation re-demonstrates that the verifier fails
   where it must and stays green where divergence is intentional, and a run that
   cannot demonstrate that reports CNO rather than PASS.

6. **Status is emitted as structured state** — `matched`, `intentional-divergence`,
   `drift`, `unresolved` — bound to the sha256 of the verifier and contract bytes,
   so the mapped-surface relationship is observable without reconstructing the
   install map from prose.

7. **What the installer actually produces is checked separately.**
   `check_stamped_substrate.py` stamps into a disposable directory and asserts
   both obligations: that the reconciled substrate arrives, and that intentional
   divergence survives. A contract correct on paper but wrong in `install.py`
   fails here.

## Consequences

A fix landing on one surface and not the other now fails CI by name, and a
deliberate difference is a reviewed declaration rather than an accident nobody
noticed. The cost is a contract that must be updated in the same commit as any
`stamp()` change — a stale transcription is worse than none, which is why the
verifier refuses unclaimed exclusions and stale declarations.

Two classes of divergence were reclassified in the process. `quality.py` and the
user-owned files are intentional and now say so. The dormant
supervisor/adapter pair is *not* intentional live-only: the install contract says
the template module tree carries all low-level logic, and B4-002 deferred
*activation*, not distribution. They are stamped together — never one without the
other, since the adapter imports the supervisor — and remain dormant. This
decision does not rewire `agent_pi`, waive the extension-transport decision, or
change the CNO/REFUSED status of Windows provider execution.
