# Security and Credential Boundary

## Host-only long-lived secrets

The current design intentionally keeps these on the host:

- exe.dev account authentication
- `OPENROUTER_PROVISIONING_KEY`

The provisioning key can mint/revoke runtime keys and must never enter a sandbox.
Its presence permits authentication to OpenRouter; it does not authorize a
mint. The mint additionally requires the head- and target-bound, one-use effect
authority defined in [`../reference/SANDBOX_PROVIDER.md`](../reference/SANDBOX_PROVIDER.md#live-host-effect-seam-authority).

## Disposable sandbox inference key

Each sandbox receives a minted OpenRouter runtime key:

- named with the `sbx-` prefix,
- bounded by a configured spend limit,
- stored separately from the run JSON,
- revoked during teardown.

A spend limit is a ceiling, not prepaid credit.
The runtime-key mint is complete only when the authoritative provisioning list
observes the minted key hash.

## Why the sandbox cannot recursively orchestrate sandboxes

The full repository may exist in the VM, but the VM lacks the host control-plane credentials.

The boundary is credential-based rather than relying on deleting orchestration files.

## Provider subprocess boundary

The B4-002 execution substrate does not inherit the operator environment. Its
caller supplies an exact environment mapping and allowlist; the strict Pi
adapter pins that allowlist to its fixed PATH/locale/temp process-mechanics set
and creates an isolated credential-free Pi settings directory. Sensitive-name
fragments provide an additional typed refusal, but safety does not depend on
enumerating every credential word. Credentials, auth homes, cookies, and tokens
are not argv, evidence, or adapter configuration. Live authentication transport
is a separate increment.

Pi stdin is closed. Ambient sessions, extensions, skills, prompt templates,
context files, project approval, model fallback, and native retries are
disabled. On Windows, execution refuses as could-not-observe until a proven Job
Object cleanup path exists.

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
