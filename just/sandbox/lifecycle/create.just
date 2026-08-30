# Phase 1 — CREATE. Host only: control plane + key mint. Nothing lands on the VM.
#
# This file is IMPORTED by the root justfile, so it shares the root's scope and
# must not repeat `set dotenv-load` / `set positional-arguments` (duplicate
# settings are a parse error). Relative paths resolve against the repo root
# because an import — unlike a `mod` — keeps the root's working directory.
#
# Strict order, and the order is the whole design: record → VM → key.
#   record first  a crash anywhere after leaves teardown a handle to work from.
#   VM before key a failed mint orphans a VM: cheap, and visible in
#                 `ssh exe.dev ls`. A failed VM after a mint orphans a key that
#                 spends money invisibly.
# Nothing here ever destroys a VM. Failures stop and print the teardown command;
# the box stays alive so it can be inspected.
#
# SDLC-L1 / control #36 LAW_1. Minting a spending runtime key is a
# configuration mutation, so it runs behind a one-use `runtime-key-mint-only`
# capability bound to this exact repository, head, key name and spend ceiling.
# OPENROUTER_PROVISIONING_KEY being in the environment is the ability to CALL
# the provisioning API; it is deliberately NOT an obligation and never an
# approval. A repository landing authorization belongs to a different purpose
# domain and can never be presented here. The mint is not believed until the
# authoritative provisioning LIST shows the new key hash.

# mint a runtime key + boot a VM for one run: just sbx lifecycle create <task-or-run-id> [--limit 200]
create RUN_ID *FLAGS:
    #!/usr/bin/env bash
    set -euo pipefail

    RR="sandbox_mount/host/run_record.py"
    LIMIT="50.00"   # dollars on the OpenRouter key; the only knob CREATE has

    # $1 is RUN_ID, the variadic FLAGS follow (root sets positional-arguments).
    shift || true
    while [ $# -gt 0 ]; do
        case "$1" in
            --limit)   LIMIT="${2:-}"; shift 2 || true ;;
            --limit=*) LIMIT="${1#*=}"; shift ;;
            *) echo "create: unknown flag '$1' (supported: --limit N)" >&2; exit 2 ;;
        esac
    done
    if ! [[ "$LIMIT" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
        echo "create: --limit must be a number of dollars, got '$LIMIT'" >&2; exit 2
    fi

    # Preflight before anything is created, so a missing dependency cannot leave
    # a half-built run behind.
    for bin in ssh curl python3; do
        command -v "$bin" >/dev/null || { echo "create: '$bin' not on PATH" >&2; exit 1; }
    done
    # HOST-ONLY secret, from .env via the root's dotenv-load. Existence is checked;
    # the value is never printed, never written to a VM, never passed over ssh.
    if [ -z "${OPENROUTER_PROVISIONING_KEY:-}" ]; then
        echo "create: OPENROUTER_PROVISIONING_KEY missing from .env (host-only, mints/revokes runtime keys)" >&2
        exit 1
    fi

    # ── 1. run id ──────────────────────────────────────────────────────────────
    # The run id becomes the VM name and the VM name becomes a public hostname,
    # so a collision is two runs fighting over one URL. Anything without the
    # -<6 hex> suffix gets run through new-id, which adds the date + entropy.
    RUN_ID="{{RUN_ID}}"
    if [[ ! "$RUN_ID" =~ -[0-9a-f]{6}$ ]]; then
        RUN_ID="$("$RR" new-id "$RUN_ID")"
    fi
    # Hostname-safe or DNS will not carry it.
    if ! [[ "$RUN_ID" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]] || [ ${#RUN_ID} -gt 63 ]; then
        echo "create: run id '$RUN_ID' is not a valid hostname label" >&2; exit 1
    fi
    echo "run id:  $RUN_ID"   # later phases all take this id — it is the handle

    # ── 2. run record (before the VM: teardown always has something to find) ───
    RECORD="$("$RR" create "$RUN_ID")"
    echo "record:  $RECORD"

    # From here on a failure leaves real resources. Never destroy anything —
    # report, stop, and say how to clean up. BODY holds the mint response (which
    # contains the secret key) so it is shredded on every exit path.
    BODY=""
    AUTH_FILE=".sandbox/runs/${RUN_ID}.runtime-key-mint.auth.json"
    _on_exit() {
        rc=$?
        if [ -n "$BODY" ]; then rm -f "$BODY"; fi
        rm -f "$AUTH_FILE"
        if [ "$rc" -ne 0 ]; then
            printf '\ncreate FAILED (exit %s). Nothing was destroyed — inspect, then:\n  just sbx lifecycle teardown %s\n' "$rc" "$RUN_ID" >&2
        fi
        exit "$rc"
    }
    trap _on_exit EXIT

    # ── 3. the VM ──────────────────────────────────────────────────────────────
    # Control plane is plain ssh; --json makes it scriptable. --tag inkwell is
    # what `reap` and bulk cleanup filter on.
    echo "vm:      creating $RUN_ID (ssh exe.dev new --tag inkwell) ..."
    VM_JSON="$(ssh exe.dev new --name "$RUN_ID" --tag inkwell --json)"

    # The exact key names of `new --json` are UNVERIFIED (only `ls --json` was
    # observed: {"vms":[{vm_name,https_url,ssh_dest,...}]}). Accept the shapes we
    # have seen and the obvious variants rather than guessing one.
    PARSED="$(printf '%s' "$VM_JSON" | python3 -c '
    import json, sys
    try:
        d = json.loads(sys.stdin.read())
    except ValueError:
        d = {}
    if isinstance(d, dict) and isinstance(d.get("vm"), dict):
        d = d["vm"]
    if isinstance(d, dict) and isinstance(d.get("vms"), list) and d["vms"]:
        d = d["vms"][0]
    if not isinstance(d, dict):
        d = {}
    print(d.get("vm_name") or d.get("name") or "")
    print(d.get("https_url") or d.get("url") or "")
    ')"
    { read -r VM_NAME || true; read -r HTTPS_URL || true; } <<< "$PARSED"

    # Fallback on an unrecognised payload: ask the one shape that IS verified.
    if [ -z "${VM_NAME:-}" ]; then
        echo "vm:      'new --json' shape unrecognised, re-reading from 'ls --json'"
        PARSED="$(ssh exe.dev ls "$RUN_ID" --json | python3 -c '
    import json, sys
    want = sys.argv[1]
    vms = (json.load(sys.stdin) or {}).get("vms") or []
    hit = next((v for v in vms if v.get("vm_name") == want), None) or {}
    print(hit.get("vm_name") or "")
    print(hit.get("https_url") or "")
    ' "$RUN_ID")"
        { read -r VM_NAME || true; read -r HTTPS_URL || true; } <<< "$PARSED"
    fi
    VM_NAME="${VM_NAME%$'\r'}"
    HTTPS_URL="${HTTPS_URL%$'\r'}"
    [ -n "${VM_NAME:-}" ] || { echo "create: could not determine the VM name for $RUN_ID" >&2; exit 1; }
    # Measured: --name becomes the public hostname, so this derivation is safe.
    [ -n "${HTTPS_URL:-}" ] || HTTPS_URL="https://${VM_NAME}.exe.xyz"

    "$RR" set "$RUN_ID" vm_name="$VM_NAME" https_url="$HTTPS_URL"
    echo "vm:      $VM_NAME  ->  $HTTPS_URL"

    # ── 4. the runtime key (LAST — see the header for why) ─────────────────────
    # The 'sbx-' prefix is load-bearing: it is how `reap` tells managed keys from
    # the engineer's personal ones. Never mint without it.
    KEY_FILE=".sandbox/runs/${RUN_ID}.key"
    KEY_NAME="sbx-$RUN_ID"
    mkdir -p .sandbox/runs

    # Typed pre-effect observations. Each is a positive read of an authoritative
    # surface — never "the env var is set", never "we got this far".
    OBL_RECORD="observed-good"
    WHY_RECORD="run record $RECORD was created by this run"
    OBL_VM="observed-good"
    WHY_VM="the control plane named vm $VM_NAME for $RUN_ID"
    OBL_LIMIT="observed-good"
    WHY_LIMIT="--limit parsed as a positive dollar amount: $LIMIT"
    PRIOR_HASH=$("$RR" get "$RUN_ID" key_hash)
    if [ -n "$PRIOR_HASH" ] || [ -e "$KEY_FILE" ]; then
        OBL_PRIOR="observed-bad"
        WHY_PRIOR="run $RUN_ID already holds a runtime key; a second mint would double the spend capability"
    else
        OBL_PRIOR="observed-good"
        WHY_PRIOR="the authoritative record carries no key_hash and no key file exists"
    fi

    MINT_RC=0
    python3 -m adws.adw_modules.sandbox_provider mint --effect runtime-key-mint-only \
        --run-id "$RUN_ID" --resource "$KEY_NAME" --param "spend_limit_usd=$LIMIT" \
        --out "$AUTH_FILE" \
        --obligation "run-record-open|$OBL_RECORD|$WHY_RECORD" \
        --obligation "provider-resource-observed|$OBL_VM|$WHY_VM" \
        --obligation "no-prior-runtime-key|$OBL_PRIOR|$WHY_PRIOR" \
        --obligation "spend-ceiling-bounded|$OBL_LIMIT|$WHY_LIMIT" || MINT_RC=$?
    if [ "$MINT_RC" -ne 0 ]; then
        echo "create: runtime-key mint authority was NOT minted (exit $MINT_RC) — no key was created." >&2
        exit 1
    fi

    GATE_RC=0
    python3 -m adws.adw_modules.sandbox_provider gate --effect runtime-key-mint-only \
        --run-id "$RUN_ID" --resource "$KEY_NAME" --param "spend_limit_usd=$LIMIT" \
        --authorization "$AUTH_FILE" || GATE_RC=$?
    if [ "$GATE_RC" -ne 0 ]; then
        echo "create: pre-effect runtime-key gate refused (exit $GATE_RC) — no key was created." >&2
        exit 1
    fi

    BODY="$(mktemp)"   # 0600 by mktemp; holds the secret until it is on disk
    CODE="$(curl -sS -o "$BODY" -w '%{http_code}' https://openrouter.ai/api/v1/keys \
        -H "Authorization: Bearer $OPENROUTER_PROVISIONING_KEY" \
        -H "Content-Type: application/json" \
        -d "$(printf '{"name": "%s", "limit": %s}' "$KEY_NAME" "$LIMIT")")"
    if [ "$CODE" != "200" ] && [ "$CODE" != "201" ]; then
        # Safe to show: a failed mint returned no key. A success is never printed.
        echo "create: OpenRouter key mint failed (HTTP $CODE): $(cat "$BODY")" >&2
        rm -f "$BODY"; exit 1
    fi

    # python writes the secret straight to disk at 0600 and prints only the hash,
    # so the key never reaches stdout, a log, or a shell variable. It also stays
    # out of the JSON record, which is greppable and gets shown in reports.
    KEY_HASH="$(python3 - "$BODY" "$KEY_FILE" <<'PY'
    import json, os, sys

    try:
        d = json.load(open(sys.argv[1]))
    except ValueError:
        sys.exit("create: OpenRouter mint response was not JSON")
    data = d.get("data") if isinstance(d.get("data"), dict) else {}
    # Observed shape is key at top level, hash under .data — accept either place.
    key = d.get("key") or data.get("key")
    key_hash = d.get("hash") or data.get("hash")
    if not key or not key_hash:
        sys.exit("create: mint response missing key/hash (top-level fields: %s)" % ", ".join(sorted(d)))
    fd = os.open(sys.argv[2], os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as fh:
        fh.write(key + "\n")
    print(key_hash)
    PY
    )"
    rm -f "$BODY"
    chmod 600 "$KEY_FILE"
    "$RR" set "$RUN_ID" key_hash="$KEY_HASH" limit="$LIMIT"

    # Post-effect: an HTTP 200 and a parsed body are the provider's word for it.
    # The provisioning LIST is the authoritative view — the same measured reason
    # teardown gates revocation on the list and never on GET /key.
    POST="could-not-observe"
    WHY_POST="the provisioning key list did not answer after the mint"
    if KEY_LIST=$(curl -sS --max-time 30 https://openrouter.ai/api/v1/keys \
            -H "Authorization: Bearer $OPENROUTER_PROVISIONING_KEY" 2>/dev/null); then
        case "$(printf '%s' "$KEY_LIST" | KH="$KEY_HASH" python3 -c \
            'import json,os,sys; print("present" if os.environ["KH"] in {k.get("hash") for k in json.load(sys.stdin).get("data",[])} else "absent")' \
            2>/dev/null || echo unreadable)" in
            present) POST="observed-good"; WHY_POST="the provisioning list carries hash $KEY_HASH" ;;
            absent)  POST="observed-bad";  WHY_POST="hash $KEY_HASH is not in the provisioning list after a 2xx mint" ;;
            *)       POST="could-not-observe"; WHY_POST="the provisioning key list was unreadable" ;;
        esac
    fi
    COMPLETE_RC=0
    python3 -m adws.adw_modules.sandbox_provider complete \
        --authorization "$AUTH_FILE" --name runtime-key-listed \
        --observed "$POST" --reason "$WHY_POST" || COMPLETE_RC=$?
    if [ "$COMPLETE_RC" -ne 0 ]; then
        echo "create: the runtime key mint is UNPROVEN: $WHY_POST" >&2
        echo "create: the key may be live. Tear the run down: just sbx lifecycle teardown $RUN_ID" >&2
        exit 1
    fi
    rm -f "$AUTH_FILE"

    echo "key:     $KEY_NAME  limit \$$LIMIT  hash $KEY_HASH"
    echo "key:     $WHY_POST"
    echo "key:     secret written to $KEY_FILE (0600) — FILL injects it"

    # ── 5. wait for ssh ────────────────────────────────────────────────────────
    # All *.exe.xyz share one host key and the wildcard known_hosts entry is
    # already installed, so BatchMode never stalls on a prompt.
    echo "ssh:     waiting for $VM_NAME.exe.xyz (up to 60s) ..."
    WAIT_START=$SECONDS
    DEADLINE=$((SECONDS + 60))
    READY=0
    while [ "$SECONDS" -lt "$DEADLINE" ]; do
        if ssh -o BatchMode=yes -o ConnectTimeout=5 "$VM_NAME.exe.xyz" true >/dev/null 2>&1; then
            READY=1; break
        fi
        sleep 2
    done
    if [ "$READY" -ne 1 ]; then
        echo "create: ssh never answered on $VM_NAME.exe.xyz within 60s" >&2
        exit 1
    fi
    echo "ssh:     up after $((SECONDS - WAIT_START))s"

    # ── 6. session id ──────────────────────────────────────────────────────────
    # `claude --session-id` demands a UUID and `--resume` needs the same one on
    # every later turn, so it is minted once, here, and lives in the record.
    SESSION_ID="$(python3 -c 'import uuid; print(uuid.uuid4())')"
    "$RR" set "$RUN_ID" session_id="$SESSION_ID"
    echo "session: $SESSION_ID"

    echo
    echo "created  $RUN_ID  (no code and no secrets on the box yet)"
    echo "next     just sbx lifecycle fill $RUN_ID"
