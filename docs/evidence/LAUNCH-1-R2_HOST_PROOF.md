# LAUNCH-1-R2 current-main successor host proof

## Exact tested source

- Repository: `sbracewell64/inkwell-agent-sandboxes-and-software-factory`
- Starts from: `991d3a64f1b96a8b9637f97060d692af3518228f`
- Tested source commit: `6dda35b74fa303fe4d9d18282ec5bae39786d809`
- Tested source tree: `1bf587608a3edb5d9f905e1ff5316cc53d86c565`
- Launcher blob: `901e4926d5d8a213da7535c739f71b5e0d779be1`
- Launcher-test blob: `64d41d56f161cf1b0f475170c61d2b9bc0477bf0`
- Predecessor PR #19 remains unchanged at `6f409ff111ddca747e76f1fde20645f98e09d7d2`; none of its host narrative is reused as this observation.

Any final candidate can use this as launcher evidence only while its launcher and
test blobs remain exactly equal to the values above. Exact-head CI and semantic
review bind separately to the final candidate head.

## Focused behavioral and host checks

From the clean tested source commit:

```text
python3 -m unittest -v tests/test_windows_front_door.py

Ran 6 tests in 1.083s
OK
```

All six tests ran with no skip on the CMD/WSL-capable host. This included the
attached/detached fixture identity, dependency refusals, transport-only source
contract, two independent Windows caller directories, default-lab refusal, and
unknown-argument refusal.

The public-sink controls were replayed explicitly so process failure could not
stand in for a watched-red result:

```text
identity state=attached rc=0 verdict=PASS
identity state=detached rc=0 verdict=PASS
watched-red field=head= rc=0 verdict=RED reason=unexpected public identity: [... handoff=firstmate head=stale]
watched-red field=branch= rc=0 verdict=RED reason=unexpected public identity: [... handoff=firstmate branch=stale]
```

The tracked launcher was then invoked directly with `--print-menu` from both
supported independent caller directories. Each returned 0, emitted exactly one
complete four-field identity line, contained neither prohibited field, and
rendered FirstMate output:

```text
caller=/mnt/c/Windows rc=0 exact_identity=PASS prohibited_absent=PASS firstmate=True
caller=/mnt/c/Users/Public rc=0 exact_identity=PASS prohibited_absent=PASS firstmate=True
```

The exact public identity owned by the assertion was:

```text
SSSF front door: project=sssf repository=sbracewell64/inkwell-agent-sandboxes-and-software-factory root=E:\SSSF handoff=firstmate
```

## Shortcut inspection

Windows PowerShell inspected the existing shortcut without modifying it:

```json
{"Path":"C:\\Users\\Public\\Desktop\\SSSF FirstMate.lnk","TargetPath":"E:\\SSSF\\bin\\sssf-firstmate.cmd","Arguments":"","WorkingDirectory":"E:\\SSSF"}
```

The tracked target did not change, so no shortcut churn was performed.

## Linux general regression gate

The repository gate ran with exact scratch-only `just 1.58.0`, `bun 1.3.14`,
and a `python` alias to the executing Python 3 interpreter. Scratch tools and
evidence were removed afterward.

```text
python3 tools/ci_gate.py run --evidence <scratch>/linux.json
ci-gate discovered=10 executed=10 conclusion=observed-good
status counts: observed-good=10 observed-bad=0 could-not-observe=0
inkwell: 30 pass, 0 fail
```

This is general Linux regression evidence. The gate manifest does not schedule
the host-topology-dependent launcher suite, so it is not represented as
launcher-specific CI proof.

## Three-valued boundaries

- **Observed-good:** exact four-field identity; successful attached/detached
  fixture handoff; effective successful-process `head=`/`branch=` watched-red
  controls; direct `--print-menu` from two Windows caller directories; existing
  shortcut target; complete Linux general gate.
- **Could-not-observe:** guarded `--detach` lifecycle. This worker's reflag did
  not carry a Herdr-lab safety scaffold, so no lifecycle command was run.
- **Could-not-observe:** final exact-head Linux/Windows forge CI,
  assignment-distinct review, and landing. They require the final successor PR
  and remain separate gates.
