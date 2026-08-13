# Freeze Procedure — SSSF-LOCAL-B0

The goal is to preserve **source, local compatibility changes, proof evidence, and provenance** without merging the disposable proof feature into the baseline.

## 1. Harvest the successful proof run before teardown

From `E:\SSSF`:

```bat
just sbx manage harvest baseline-proof-20260813-d38790
```

Verify:

```bat
git log -1 --oneline refs/sandbox/baseline-proof-20260813-d38790
```

Expected proof head includes commit `042dfb9`.

Do not merge this proof ref into `main`. It is evidence.

## 2. Preserve run evidence

Before destruction, retain the run record and trace artifacts. Teardown is designed to harvest artifacts before revoke/destroy.

Run:

```bat
just sbx lifecycle teardown baseline-proof-20260813-d38790
```

Then verify:

```bat
just sbx manage list
ssh exe.dev ls
```

The run should be closed and the VM gone.

Record the artifact directory under `.sandbox/runs/` if created.

## 3. Remove temporary source backup

The temporary file `just/sandbox/lifecycle/create.just.stock` is not needed because upstream Git already preserves the original.

```bat
del just\sandbox\lifecycle\create.just.stock
```

## 4. Create a baseline branch

Do not commit directly to upstream-tracking `main`.

```bat
git switch -c local/sssf-baseline-b0
```

## 5. Commit the Windows compatibility changes separately

```bat
git add just/sandbox/lifecycle/create.just
git commit -m "fix(windows): normalize sandbox VM metadata"

git add just/sandbox/lifecycle/teardown.just
git commit -m "fix(windows): make teardown temp files portable"
```

This preserves each causal fix as its own increment.

## 6. Add and commit the documentation system

Copy this `docs/` directory to the repository root, then:

```bat
git add docs
git commit -m "docs: establish proven SSSF baseline"
```

## 7. Record exact immutable objects

Run:

```bat
git rev-parse HEAD
git rev-parse refs/sandbox/baseline-proof-20260813-d38790
git status --short
```

Update `docs/baseline/BASELINE.md` if any recorded SHA differs from the values currently written.

The working tree must be clean before tagging.

## 8. Tag the accepted baseline

```bat
git tag -a sssf-local-b0 -m "Proven local SSSF baseline B0"
```

Verify:

```bat
git show --no-patch --decorate sssf-local-b0
```

The tag is the immutable answer to: **what exactly was the trusted local SSSF baseline?**

## 9. Optional remote preservation

If you create a personal fork/remote later, push the branch, tag, and proof ref only after verifying the destination:

```bat
git push <your-remote> local/sssf-baseline-b0
git push <your-remote> sssf-local-b0
```

The proof ref may be pushed under a clearly named evidence branch if desired; never pretend it is baseline source.

## Freeze completion criteria

B0 is frozen only when:

- successful sandbox proof is harvested,
- sandbox is torn down and key revoked,
- run record is closed,
- compatibility fixes are committed separately,
- documentation is committed,
- working tree is clean,
- annotated tag `sssf-local-b0` exists,
- exact source and proof SHAs are recorded.
