# Source-of-Truth Policy

## Precedence

When deciding what the system actually does:

1. **Executable source + deterministic tests**
2. **Immutable Git objects + captured run evidence**
3. **Current config files**
4. **`docs/`**
5. **README/TREE/skills/cookbooks**
6. **generated specs/app docs**
7. **chat history**

Chat is never the durable source of truth.

## Documentation mismatch

If docs conflict with code:

- do not silently edit one to match your assumption,
- identify which behavior is intended,
- create an increment,
- prove the correction,
- update both code and docs as required.

## Generated material

`specs/` and `app_docs/` are evidence/history produced by runs. They may explain why a change was made, but they do not automatically define current runtime behavior.

## Baseline records

Baseline documents must reference exact Git SHAs and run identities wherever possible.
