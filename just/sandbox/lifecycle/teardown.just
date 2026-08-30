# Phase 6 — TEARDOWN. Host only, and only when we decide.
#
# IMPORTED into the root justfile (not a module): no `set` lines here, and the
# root's `set dotenv-load` is what puts OPENROUTER_PROVISIONING_KEY in scope.
# No file-level variables either — six imports share one scope, so a duplicate
# name across phase files is a hard error. Everything is a bash local instead.
#
# Order is load-bearing: spend captured -> artifacts out -> commits harvested ->
# key revoked -> VM destroyed. A crash between revoke and destroy leaves a dead
# key and a live VM (visible, cheap). The reverse leaves a live key nobody can
# find (invisible, spends). This is the ONLY file allowed to destroy a VM.
#
# Everything that READS the box runs before anything that destroys it, and the
# harvest failing ABORTS the whole teardown: destroying a VM whose commits were
# never pulled is the one irreversible mistake available in this file.
#
# SDLC-L1 / control #36 LAW_1. Reaching step 5 is ORDERING, not authority, so
# each step above records a TYPED three-valued observation and destruction runs
# only behind a one-use `destroy-only` capability minted from those observations
# and bound to this exact repository, head, and VM. A repository landing
# authorization lives in a different purpose domain and can never be presented
# here. `--no-harvest` is therefore no longer approval: it makes the harvest
# obligation could-not-observe, no authority is minted, and the VM is left
# alive. The only way past it is to harvest, or to have a record that positively
# proves FILL never ran and there is nothing to harvest.
#
# IDEMPOTENT by construction: every step is individually guarded, because a run
# can die anywhere — VM but no key, key but no VM, a record with neither. A
# missing piece is the normal path, not an error.

# tear down one run: spend -> artifacts -> harvest -> revoke -> destroy -> close -> gate
teardown RUN_ID *FLAGS:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{ justfile_directory() }}"

    RR="sandbox_mount/host/run_record.py"
    RUN_ID="{{ RUN_ID }}"
    RUNS=".sandbox/runs"
    KEY_FILE="$RUNS/$RUN_ID.key"
    ART="$RUNS/$RUN_ID-artifacts"
    API="https://openrouter.ai/api/v1"
    AUTH_FILE="$RUNS/$RUN_ID.destroy.auth.json"

    # Through a variable, not straight into `for ... in`: interpolating an empty
    # variadic into the list is a syntax error, via a variable it is zero iterations.
    RAW_FLAGS="{{ FLAGS }}"
    HARVEST=1
    for a in $RAW_FLAGS; do
        case "$a" in
            --no-harvest) HARVEST=0 ;;
            *) echo "teardown: unknown flag $a (only --no-harvest)"; exit 2 ;;
        esac
    done
    # All *.exe.xyz share one host key and a wildcard known_hosts entry is already
    # installed, so no StrictHostKeyChecking games. BatchMode so a teardown never
    # sits at a password prompt; timeouts so it never hangs on a dead VM.
    SSH_OPTS=(-o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=10 -o ServerAliveCountMax=3)

    echo "── teardown $RUN_ID"

    # The record is the only handle on the key. Without it there is nothing to
    # revoke and nothing to close, so this is the one hard prerequisite.
    "$RR" get "$RUN_ID" > /dev/null || { echo "!! no run record for $RUN_ID — nothing to tear down"; exit 1; }
    VM=$("$RR" get "$RUN_ID" vm_name)
    KEY_HASH=$("$RR" get "$RUN_ID" key_hash)
    COMMIT_SHA=$("$RR" get "$RUN_ID" commit_sha)
    CLOSED=$("$RR" get "$RUN_ID" closed_at)
    [ -n "$CLOSED" ] && echo "   (record already closed at $CLOSED — re-running the remaining steps)"

    # Reads the control plane once and names present/absent/unreadable, so an
    # unreachable listing can never be narrowed into "the VM is gone".
    vm_listed() {
        printf '%s' "$1" | VM="$2" python3 -c \
            'import json,os,sys; print("present" if os.environ["VM"] in {v.get("vm_name") for v in json.load(sys.stdin).get("vms",[])} else "absent")' \
            2>/dev/null || echo unreadable
    }

    # ── does the VM still exist? -------------------------------------------------
    # Ask the control plane rather than probing ssh: authoritative, and the same
    # answer `reap` uses. Verified shape: {"vms":[{"vm_name":"...",...}]}
    VM_ALIVE=0
    OBL_VM="could-not-observe"
    WHY_VM="the control plane was never asked"
    if [ -z "$VM" ]; then
        OBL_VM="observed-good"; WHY_VM="the run record names no vm for this run"
    elif VM_LIST=$(ssh "${SSH_OPTS[@]}" exe.dev ls --json 2>/dev/null); then
        case "$(vm_listed "$VM_LIST" "$VM")" in
            present) VM_ALIVE=1; OBL_VM="observed-good"; WHY_VM="the control plane lists $VM" ;;
            absent)  OBL_VM="observed-good"; WHY_VM="the control plane does not list $VM" ;;
            *)       OBL_VM="could-not-observe"; WHY_VM="the control plane listing was unreadable" ;;
        esac
    else
        OBL_VM="could-not-observe"; WHY_VM="ssh exe.dev ls --json did not answer"
    fi
    if [ "$VM_ALIVE" = 1 ]; then echo "   vm:  $VM (running)"; else echo "   vm:  ${VM:-<none>} ($WHY_VM)"; fi

    # ── 1. spend, BEFORE the key dies -------------------------------------------
    # This is what makes best-of-N comparable: same prompt, N models, cost beside
    # result. Read it now — after DELETE the number is unrecoverable.
    # NOTE: the runtime key is a SANDBOX secret; the provisioning key never leaves
    # this host and is never used for the per-key usage read.
    SPEND=""
    if [ -s "$KEY_FILE" ]; then
        RUNTIME_KEY=$(cat "$KEY_FILE")
        # GET /api/v1/key reports the calling key's own usage. Verified shape:
        # {"data":{"usage":0.0081,"limit":50.0,...}}
        SPEND=$(curl -sS --max-time 30 "$API/key" -H "Authorization: Bearer $RUNTIME_KEY" 2>/dev/null \
                | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"]["usage"])' 2>/dev/null || true)
        unset RUNTIME_KEY
    elif [ -n "$KEY_HASH" ] && [ -n "${OPENROUTER_PROVISIONING_KEY:-}" ]; then
        # Re-run after the .key file was already shredded: the provisioning LIST
        # still carries `usage` per hash, so spend is recoverable from there.
        SPEND=$(curl -sS --max-time 30 "$API/keys" -H "Authorization: Bearer $OPENROUTER_PROVISIONING_KEY" 2>/dev/null \
                | KH="$KEY_HASH" python3 -c \
                  'import json,os,sys; print(next((k["usage"] for k in json.load(sys.stdin).get("data",[]) if k.get("hash")==os.environ["KH"]), ""))' 2>/dev/null || true)
    fi
    if [ -n "$SPEND" ]; then
        "$RR" set "$RUN_ID" spend="$SPEND"
        echo "   spend: \$$SPEND recorded"
        OBL_SPEND="observed-good"; WHY_SPEND="usage \$$SPEND recorded before the key died"
    elif [ -z "$KEY_HASH" ]; then
        echo "   spend: n/a — no key was ever minted for this run"
        OBL_SPEND="observed-good"; WHY_SPEND="the record positively shows no key was ever minted"
    else
        echo "   spend: unavailable (key file gone, hash no longer listed) — leaving record as-is"
        OBL_SPEND="could-not-observe"; WHY_SPEND="usage for $KEY_HASH could not be read"
    fi

    # ── 2. artifacts ------------------------------------------------------------
    OBL_ART="observed-good"
    WHY_ART="no vm, so there is nothing on a box to collect"
    if [ "$VM_ALIVE" = 1 ]; then
        mkdir -p "$ART"
        TAR_TMP=$(mktemp -t "sbx-$RUN_ID.XXXXXX")
        # One round trip, and `ls -d` filters to what actually exists so a run that
        # died before writing app_docs/ is not an error. A transport failure is a
        # separate answer from "the box had nothing", so the exit status is kept.
        TAR_RC=0
        ssh "${SSH_OPTS[@]}" "$VM".exe.xyz \
            'cd app 2>/dev/null || exit 0; P=$(ls -d specs app_docs adws/adw_data/sssf.db run.log 2>/dev/null); [ -z "$P" ] && exit 0; tar cf - $P' \
            > "$TAR_TMP" || TAR_RC=$?
        if [ "$TAR_RC" -ne 0 ]; then
            echo "   artifacts: collection could not be observed (ssh exited $TAR_RC)"
            OBL_ART="could-not-observe"; WHY_ART="the artifact read from $VM exited $TAR_RC"
            rmdir "$ART" 2> /dev/null || true
        elif [ -s "$TAR_TMP" ]; then
            tar xf "$TAR_TMP" -C "$ART"
            echo "   artifacts -> $ART"
            OBL_ART="observed-good"; WHY_ART="artifacts extracted to $ART"
        else
            echo "   artifacts: none found on the vm"
            rmdir "$ART" 2> /dev/null || true   # do not leave an empty dir implying we pulled something
            OBL_ART="observed-good"; WHY_ART="the box positively reported no artifact paths"
        fi
        rm -f "$TAR_TMP"
    else
        echo "   artifacts: skipped (no vm)"
    fi

    # ── 3. harvest the commits --------------------------------------------------
    # File copies LOSE history, and SSSF commits plan, code and docs as separate
    # commits — the shape of the run is in the commit graph, not the files. The
    # bundling lives in harvest.just so it can also be run on its own, at any time,
    # without committing to a teardown. Default ON here so nobody loses a run's work
    # by forgetting; a failure STOPS before revoke and destroy.
    OBL_HARVEST="observed-good"
    WHY_HARVEST="no vm, so there are no commits on a box to pull"
    if [ "$HARVEST" != 1 ]; then
        if [ -z "$COMMIT_SHA" ]; then
            # Not a marker: the authoritative record positively shows FILL never
            # completed, so no commit ever existed on that box to lose.
            echo "   harvest: skipped (--no-harvest; the record shows FILL never completed)"
            OBL_HARVEST="observed-good"; WHY_HARVEST="the record has no commit_sha, so FILL never staged a source head"
        else
            echo "   harvest: skipped (--no-harvest) — the run's commits were NOT observed"
            OBL_HARVEST="could-not-observe"; WHY_HARVEST="--no-harvest skipped the pull for a run whose FILL head is $COMMIT_SHA"
        fi
    elif [ "$VM_ALIVE" = 1 ]; then
        just sbx manage harvest "$RUN_ID" || {
            echo "!! harvest FAILED — stopping before revoke and destroy. The VM is left alive."
            echo "!! diagnose, then re-run:      just sbx lifecycle teardown $RUN_ID"
            exit 1
        }
        OBL_HARVEST="observed-good"; WHY_HARVEST="just sbx manage harvest $RUN_ID succeeded"
    else
        echo "   harvest: skipped (no vm)"
    fi

    # ── 4. revoke the key -------------------------------------------------------
    OBL_KEY="observed-good"
    WHY_KEY="the record positively shows no key was ever minted"
    if [ -z "$KEY_HASH" ]; then
        echo "   key: none minted for this run — nothing to revoke"
    elif [ -z "${OPENROUTER_PROVISIONING_KEY:-}" ]; then
        echo "!! key_hash $KEY_HASH is live but OPENROUTER_PROVISIONING_KEY is unset — cannot revoke."
        echo "!! set it in .env and re-run: a live key keeps spending. VM left alone."
        exit 1
    else
        CODE=$(curl -sS --max-time 30 -o /dev/null -w '%{http_code}' -X DELETE "$API/keys/$KEY_HASH" \
               -H "Authorization: Bearer $OPENROUTER_PROVISIONING_KEY")
        case "$CODE" in
            2*)  echo "   key: revoked ($KEY_HASH)"
                 OBL_KEY="observed-good"; WHY_KEY="DELETE $API/keys/$KEY_HASH returned $CODE" ;;
            404) echo "   key: already gone ($KEY_HASH)"   # idempotent re-run
                 OBL_KEY="observed-good"; WHY_KEY="the key was already absent (404)" ;;
            *)   echo "!! DELETE $API/keys/$KEY_HASH returned $CODE — key may still be live. VM left alone."; exit 1 ;;
        esac
    fi

    # ── 5. destroy the vm, under typed one-use authority ------------------------
    # control #36 LAW_1. Everything above produced a NAMED three-valued
    # observation; those observations, and only those, mint a `destroy-only`
    # capability bound to this repository, this head, and this exact VM. The gate
    # then spends it once. Nothing about reaching this line, and no flag or
    # environment variable, is approval.
    if [ "$VM_ALIVE" = 1 ]; then
        MINT_RC=0
        python3 -m adws.adw_modules.sandbox_provider mint --effect destroy-only \
            --run-id "$RUN_ID" --resource "$VM" --out "$AUTH_FILE" \
            --obligation "vm-presence|$OBL_VM|$WHY_VM" \
            --obligation "spend-recorded|$OBL_SPEND|$WHY_SPEND" \
            --obligation "artifacts-collected|$OBL_ART|$WHY_ART" \
            --obligation "commits-harvested|$OBL_HARVEST|$WHY_HARVEST" \
            --obligation "runtime-key-retired|$OBL_KEY|$WHY_KEY" || MINT_RC=$?
        if [ "$MINT_RC" -ne 0 ]; then
            echo "!! destroy authority was NOT minted (exit $MINT_RC) — $VM is left ALIVE." >&2
            echo "!! An unobserved or contradicted obligation above is why. Resolve it and re-run:" >&2
            echo "!!   just sbx manage harvest $RUN_ID  &&  just sbx lifecycle teardown $RUN_ID" >&2
            exit 1
        fi

        GATE_RC=0
        python3 -m adws.adw_modules.sandbox_provider gate --effect destroy-only \
            --run-id "$RUN_ID" --resource "$VM" --authorization "$AUTH_FILE" || GATE_RC=$?
        if [ "$GATE_RC" -ne 0 ]; then
            echo "!! pre-effect destroy gate refused (exit $GATE_RC) — $VM is left ALIVE." >&2
            exit 1
        fi

        DESTROY_RC=0
        ssh "${SSH_OPTS[@]}" exe.dev rm "$VM" > /dev/null || DESTROY_RC=$?

        # Post-effect: a provider acknowledgement is not clean terminal state.
        # Absence is claimed only when the control plane authoritatively says so.
        POST="could-not-observe"
        WHY_POST="the control plane did not answer after the destroy call"
        if AFTER_LIST=$(ssh "${SSH_OPTS[@]}" exe.dev ls --json 2>/dev/null); then
            case "$(vm_listed "$AFTER_LIST" "$VM")" in
                absent)  POST="observed-good"; WHY_POST="the control plane no longer lists $VM" ;;
                present) POST="observed-bad";  WHY_POST="$VM is still listed after rm — residual resource" ;;
                *)       POST="could-not-observe"; WHY_POST="the control plane listing was unreadable" ;;
            esac
        fi
        COMPLETE_RC=0
        python3 -m adws.adw_modules.sandbox_provider complete \
            --authorization "$AUTH_FILE" --name vm-absent \
            --observed "$POST" --reason "$WHY_POST" || COMPLETE_RC=$?
        if [ "$COMPLETE_RC" -ne 0 ]; then
            echo "!! destroy is UNPROVEN: $WHY_POST (rm exited $DESTROY_RC)." >&2
            echo "!! The record is left OPEN and the capability stays reserved for reconciliation." >&2
            echo "!! Re-run once the control plane answers: just sbx lifecycle teardown $RUN_ID" >&2
            exit 1
        fi
        rm -f "$AUTH_FILE"
        echo "   vm: destroyed ($VM) — $WHY_POST"
    else
        echo "   vm: nothing to destroy"
    fi

    # ── 6. close the record, shred the key file ---------------------------------
    "$RR" close "$RUN_ID"
    if [ -e "$KEY_FILE" ]; then
        # shred where available, `rm -P` on macOS; -f last so a re-run never fails
        # on an already-removed file.
        if command -v shred > /dev/null 2>&1; then shred -u "$KEY_FILE" 2>/dev/null || rm -f "$KEY_FILE"
        else rm -Pf "$KEY_FILE" 2>/dev/null || rm -f "$KEY_FILE"; fi
        echo "   key file shredded"
    fi
    echo "   record closed"

    # ── 7. GATE: the key is ABSENT from the key LIST ----------------------------
    # MEASURED: right after a successful DELETE, GET /api/v1/key still returns 200
    # for the dead key. The LIST is the authoritative view. Never gate on /key.
    if [ -z "$KEY_HASH" ]; then
        echo "✓ teardown complete for $RUN_ID (no key was ever minted)"
        exit 0
    fi
    LIST=$(curl -sS --max-time 30 "$API/keys" -H "Authorization: Bearer $OPENROUTER_PROVISIONING_KEY") \
        || { echo "!! gate: could not read $API/keys — revocation UNVERIFIED"; exit 1; }
    if printf '%s' "$LIST" | KH="$KEY_HASH" python3 -c \
        'import json,os,sys; sys.exit(1 if os.environ["KH"] in {k.get("hash") for k in json.load(sys.stdin).get("data",[])} else 0)'
    then
        echo "✓ gate: key absent from $API/keys"
        echo "✓ teardown complete for $RUN_ID"
    else
        echo "!! gate FAILED: $KEY_HASH is still listed at $API/keys. The key is LIVE."
        echo "!! revoke it by hand: curl -X DELETE $API/keys/$KEY_HASH -H 'Authorization: Bearer \$OPENROUTER_PROVISIONING_KEY'"
        exit 1
    fi
