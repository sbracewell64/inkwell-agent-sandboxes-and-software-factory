# B3-005 Browser Sol Ruling Provenance

**Ruling:** `WINDOWS_NATIVE_EQUIVALENCE = PASS`
**Scope:** commissioned environment-freshness condition only
**Exact reviewed head:** `63bc5792e0db4d6fb152a947648e161ae47f1b14`
**Overall B3-005:** `CNO / HOLD`
**Mode:** `PRE_CERTIFICATION`

## Provenance

- Equivalence submission: https://github.com/sbracewell64/firstmate-sol-control/issues/3#issuecomment-5302981383
- Browser Sol ruling: https://github.com/sbracewell64/firstmate-sol-control/issues/3#issuecomment-5303198972
- Exact-head PR review: https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory/pull/1#pullrequestreview-4944257620

Browser Sol's source/equivalence review binds exact reviewed head:

`63bc5792e0db4d6fb152a947648e161ae47f1b14`

The ruling accepts the documented combination of:

- `CreateEnvironmentBlock(current-user-token, inherit=false)`;
- clearing and repopulating `ProcessStartInfo.EnvironmentVariables` only from that native block;
- `UseShellExecute=false`;
- absolute Windows `cmd.exe`;
- pre-bootstrap Git `bin`/`usr\bin` absence;
- pre-bootstrap `sh`/`cygpath`/`zsh` non-resolution;
- root `just` and `just local` before bootstrap;
- bootstrap-only introduction of required Git Bash session paths;
- unchanged persistent HKCU/HKLM environment values.

## Exact scope

PASS means only that the automated method is equivalent for proving a native current-user process environment independent of inherited FirstMate, WSL, or prior SSSF process augmentation.

It does not claim equivalence for every GUI, Explorer, Start-menu, desktop, or interactive-session property.

## Holds preserved

The ruling does not promote any independent unavailable dimension:

- roster availability: `CNO / HOLD` from insufficient credits;
- typed final C/D/E completion marker: `CNO / HOLD`;
- OBSERVE: `CNO / HOLD`;
- end-to-end B3-005 portability: `CNO / HOLD`;
- GitHub CI: `CNO` because no checks are configured;
- merge, canonical-main advancement, tag creation, and final B3 freeze: `HOLD / NOT PERFORMED`.

`OVERALL_B3_005` therefore remains exactly `CNO / HOLD`.

## Provenance-only successor rule

This ruling and exact-candidate review bind `63bc5792e0db4d6fb152a947648e161ae47f1b14`. The commit adding this provenance record is a documentation-only successor. It still requires an applicability confirmation or exact-successor review before the ruling may be used for any stronger purpose. The successor does not authorize merge, main advancement, tag creation, freeze, or promotion of any held dimension.
