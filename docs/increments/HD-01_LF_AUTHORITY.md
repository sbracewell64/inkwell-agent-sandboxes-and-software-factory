# HD-01 — One Authoritative Strict LF Contract

**Status:** IMPLEMENTED WITH DETERMINISTIC PROOF
**Starts from:** `04e5484a6190f033d25e1626b96a4cca93b7f755`
**Scope:** line-ending policy, validator, Windows doctor/bootstrap integration,
operator remediation, and owned contract documentation only

## Intent

The repository policy promised LF text on every platform, but the validator
made working-tree LF optional and the Windows host doctor invoked that weaker
mode. An older checkout could therefore retain CRLF in execution-sensitive
files while policy, effective attributes, and index state were all correct and
the doctor printed a line-ending success.

HD-01 chooses the already-documented strict supported-worktree contract rather
than weakening the promise: watched execution-sensitive files must be
`i/lf w/lf` under effective `text=auto eol=lf` attributes.

This increment does not change sandbox lifecycle, DSH/migration/expansion,
credentials, proof records, model behavior, or the B3-005 lane.

## Reproduction

A disposable clone of the exact base was given a CRLF-materialized `justfile`
without changing the policy or index. Deterministic observations were:

```text
justfile: text: auto
justfile: eol: lf
i/lf    w/crlf  attr/text=auto eol=lf  justfile
```

The default validator printed PASS, and the host doctor printed its
line-ending check as `ok`. The explicit strict invocation rejected
`w/crlf`. This establishes:

- **trigger:** a watched file materialized as CRLF;
- **mask:** repository attributes and index remained LF while default/doctor
  omitted the worktree requirement;
- **operator symptom:** host validation certified the line-ending sub-check
  even though strict execution-sensitive state was red.

The reproduction used only a disposable fixture. It did not rewrite the
contribution working tree or any canonical/proof checkout.

## Design and ownership

`.gitattributes` retains one active rule:

`* text=auto eol=lf`

`docs/validation/check_line_endings.py` is the sole executable validator owner.
It always enforces policy, effective attributes, index LF, and worktree LF. The
operator-facing explicit spelling is:

`python docs/validation/check_line_endings.py --require-worktree-lf`

The option no longer selects a stronger mode; omitting it cannot weaken the
check. The Windows host doctor invokes that exact strict owner, and bootstrap
output names the same invocation.

Evidence is three-valued:

- a positively observed mismatch is `observed-bad` and produces `FAIL`;
- missing, unreadable, empty, or malformed evidence is
  `could-not-observe` and produces `CNO` when no positive mismatch exists;
- only complete matching evidence produces `PASS`.

Any mixture containing a positive mismatch is `FAIL`, while every included CNO
fact remains visible. No non-passing path prints PASS.

## Explicit remediation

Validation and bootstrap never rewrite a working tree. The operator must first
save or commit local work and require this to be empty:

`git status --short`

Then the watched files may be explicitly re-materialized from the unchanged
index:

`git checkout-index --force -- .gitattributes justfile just/sandbox/lifecycle/fill.just just/sandbox/lifecycle/setup.just sandbox_mount/guest/provision.sh sandbox_mount/host/run_record.py docs/baseline/PROOF_MATRIX.md`

Finally rerun the strict invocation. `checkout-index` changes worktree
materialization, not index contents. The clean-tree precondition prevents loss
of developer content. The deterministic test records the index tree before and
after repair and requires equality.

## Deterministic proof

`docs/validation/test_line_endings.py` is red-capable and first watches a green
fixture before each negative mutation. It proves:

1. CRLF makes both default validation and the doctor-owned check terminal
   non-PASS with `observed-bad` evidence.
2. A missing watched file is terminal non-PASS with
   `could-not-observe` evidence.
3. A wrong effective attribute is terminal non-PASS with `observed-bad`
   evidence.
4. Explicit re-materialization restores LF while preserving the index tree and
   a clean Git status.
5. A fresh disposable clone created with hostile `core.autocrlf=true`
   materializes every representative file as
   `i/lf w/lf attr/text=auto eol=lf` and passes the strict owner.

Focused proof command:

`python docs/validation/test_line_endings.py -v`

Repository-state proof command:

`python docs/validation/check_line_endings.py --require-worktree-lf`

## Acceptance

- One active policy rule and one validator owner remain.
- Default and explicit validator calls enforce the same strict worktree state.
- Windows doctor/bootstrap-facing output and owned docs name the exact strict
  invocation.
- CRLF, missing files, and wrong attributes cannot print PASS.
- Failure output retains observed-bad/could-not-observe evidence.
- Representative compliant index/worktree states pass.
- Hostile-autocrlf fresh clone and watched-red controls are executable tests.
- Remediation is explicit, deterministic, index-preserving, and never an
  automatic side effect.

**Result: PASS**

## Boundedness delta

```text
boundedness_delta: none
boundedness_reason: this increment predates the boundedness registry. Its
  growth surfaces, where it created any, were inventoried and bound
  retrospectively by BOUND-1 against the post-increment source rather than
  claimed here after the fact. See
  docs/reference/BOUNDEDNESS_REGISTRY.json and
  docs/development/BOUNDEDNESS_LAW.md.
```
