# Security and Credential Boundary

## Host-only long-lived secrets

The current design intentionally keeps these on the host:

- exe.dev account authentication
- `OPENROUTER_PROVISIONING_KEY`

The provisioning key can mint/revoke runtime keys and must never enter a sandbox.

## Disposable sandbox inference key

Each sandbox receives a minted OpenRouter runtime key:

- named with the `sbx-` prefix,
- bounded by a configured spend limit,
- stored separately from the run JSON,
- revoked during teardown.

A spend limit is a ceiling, not prepaid credit.

## Why the sandbox cannot recursively orchestrate sandboxes

The full repository may exist in the VM, but the VM lacks the host control-plane credentials.

The boundary is credential-based rather than relying on deleting orchestration files.

## Agent write security

`tools:` is capability, not path security.

An agent with `bash` or `write` can potentially touch broad paths. Therefore SSSF enforces:

- `writes:` per agent,
- `protected_files` roster-wide,
- post-call rollback of unauthorized writes.

The baseline proved rollback of an unauthorized planner edit to the Inkwell app.

## Future sandbox-provider rule

A replacement for exe.dev must preserve:

- isolation from host filesystem,
- no host provisioning credential in guest,
- bounded runtime secret,
- recoverable lifecycle identity,
- explicit teardown,
- artifact/commit extraction before destruction.
