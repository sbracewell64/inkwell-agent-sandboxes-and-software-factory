# just/sandbox/setup.just — PHASE 3 of 6: SETUP.
#
# Imported by the root justfile (not a module), so it shares the root's scope
# and settings. No `set` lines here on purpose: duplicating `dotenv-load` or
# `positional-arguments` is a hard error at parse time.
#
# What this phase does: run provision.sh inside the sandbox, wait for its
# sentinel, then run the five-assertion health gate. Nothing here creates or
# destroys a VM. On failure it prints how to get into the box and exits
# non-zero, because a gate that auto-destroys throws away the evidence.
#
# The OpenRouter PROVISIONING key never appears in this file. The gate spends
# money, so it uses the disposable RUNTIME key — which already lives on the VM
# in app/.env (written in FILL). That is why assertions C/D/E execute inside the
# sandbox: the key never has to travel, and the gate proves the sandbox's own
# egress works rather than the host's.

# CONFIG picks which roster assertion C pings, and defaults to the starter
# roster. It has to be an ARGUMENT: C used to read $SSSF_CONFIG out of the
# remote environment, but `ssh host 'cmd'` carries no environment at all, so
# that read always fell through to the default. On a fan-out where each arm runs
# a different roster, every arm was gated against models it would never call —
# the gate passed and told you nothing. Pass the same path here that you pass to
# `just sbx lifecycle execute`.

# phase 3: provision the sandbox, then gate it (never destroys the VM). CONFIG picks the roster C pings
setup RUN_ID CONFIG="":
    #!/usr/bin/env bash
    set -euo pipefail

    RR="sandbox_mount/host/run_record.py"
    VM=$("$RR" get {{RUN_ID}} vm_name)
    SOURCE_REPO=$("$RR" get {{RUN_ID}} source_repo)
    SOURCE_SHA=$("$RR" get {{RUN_ID}} source_sha)
    SHA=$("$RR" get {{RUN_ID}} commit_sha)

    # run_record prints an empty line for an unset field, so emptiness is the
    # real check — a missing vm_name means CREATE never finished.
    [ -n "$VM" ]  || { echo "[setup] run record {{RUN_ID}} has no vm_name — run: just sbx lifecycle create {{RUN_ID}}" >&2; exit 1; }
    [ -n "$SHA" ] || { echo "[setup] run record {{RUN_ID}} has no commit_sha — run: just sbx lifecycle fill {{RUN_ID}}" >&2; exit 1; }
    [ -n "$SOURCE_REPO" ] || {
        echo "[setup] run record {{RUN_ID}} has no source_repo — run FILL again" >&2
        exit 1
    }
    [ -n "$SOURCE_SHA" ] || {
        echo "[setup] run record {{RUN_ID}} has no source_sha — run FILL again" >&2
        exit 1
    }
    [ "$SOURCE_SHA" = "$SHA" ] || {
        echo "[setup] source_sha $SOURCE_SHA != commit_sha $SHA" >&2
        exit 1
    }

    HOST="$VM.exe.xyz"
    # ConnectTimeout only: every *.exe.xyz shares one host key and the wildcard
    # known_hosts entry is already installed, so ssh is non-interactive already.
    SSH=(ssh -o ConnectTimeout=15 "$HOST")

    echo "[setup] run {{RUN_ID}}  vm ${VM}"
    echo "[setup] source repo ${SOURCE_REPO}"
    echo "[setup] source sha  ${SOURCE_SHA}"

    # Every failure below routes through here: report, hand over the debug
    # command, exit non-zero. NEVER destroy — teardown stays an explicit choice.
    gate_fail() {
      echo ""
      echo "[setup] FAILED: $*" >&2
      echo "[setup] the VM is still running on purpose — the evidence is on the box:" >&2
      echo "[setup]   ssh ${HOST}" >&2
      echo "[setup]   ssh ${HOST} 'cd app && git status --porcelain'" >&2
      echo "[setup]   ssh ${HOST} 'pi --list-models'" >&2
      echo "[setup] tear it down only when you are done: just sbx lifecycle teardown {{RUN_ID}}" >&2
      exit 1
    }

    # ── 1. provision ─────────────────────────────────────────────────────────
    # Clear the sentinel first: re-running setup on the same VM would otherwise
    # find the PREVIOUS run's sentinel and declare victory before provision ran.
    echo "[setup] 1/3 provisioning (streaming provision.sh output)"
    "${SSH[@]}" 'rm -f /tmp/PROVISION_READY' < /dev/null \
      || gate_fail "cannot reach ${HOST} over ssh"
    # < /dev/null so ssh does not swallow this script's stdin; output streams live.
    "${SSH[@]}" 'bash app/sandbox_mount/guest/provision.sh' < /dev/null \
      || gate_fail "provision.sh exited non-zero (its last '── step ──' line names the stage)"

    # ── 2. sentinel ──────────────────────────────────────────────────────────
    # provision.sh touches /tmp/PROVISION_READY as its literal last line, so on
    # this synchronous path the file is already there and the loop exits on the
    # first probe. The poll is bounded anyway: it is the only completion signal
    # that stays correct if provision is ever backgrounded, and an unbounded
    # wait on a dead box is a hang, not a failure.
    echo "[setup] 2/3 waiting for /tmp/PROVISION_READY (max 60s)"
    ready=0
    for _ in $(seq 1 30); do
      if "${SSH[@]}" 'test -f /tmp/PROVISION_READY' < /dev/null; then ready=1; break; fi
      sleep 2
    done
    [ "$ready" -eq 1 ] || gate_fail "sentinel /tmp/PROVISION_READY never appeared"
    echo "[setup]     sentinel present"

    # ── 3. the gate ──────────────────────────────────────────────────────────
    echo "[setup] 3/3 health gate (5 assertions)"

    # A — git integrity. Content, not existence: an unsynced golden-VM clone
    # produced 5,641 zero-byte files and reported success, and truncation shows
    # up as ' M path'. Expected-vs-actual SHA is compared by prefix so a short
    # commit_sha in the record still matches a full HEAD.
    #
    # The tree must be CLEAN. Nothing legitimately dirties it: the sandbox
    # clones the repo and provisions around it, so any porcelain line at all
    # means something wrote where it should not have.
    echo "[gate] A git integrity"
    if "${SSH[@]}" 'bash -s' "$SHA" "$SOURCE_REPO" <<'REMOTE_A'; then
    set -uo pipefail
    cd "$HOME/app" || { echo "   no ~/app on this VM — FILL never ran"; exit 1; }
    want="${1:-}"
    want_repo="${2:-}"
    head="$(git rev-parse HEAD)" || { echo "   git rev-parse failed — .git is damaged"; exit 1; }
    origin="$(git remote get-url origin)" || {
      echo "   git remote get-url origin failed"
      exit 1
    }
    echo "   origin   ${origin}"
    echo "   expected ${want_repo}"
    [ "$origin" = "$want_repo" ] || {
      echo "   origin does not match recorded source_repo"
      exit 1
    }
    echo "   HEAD     ${head}"
    echo "   expected ${want}"
    case "$head" in
      "$want"*) ;;
      *) echo "   HEAD does not match the recorded commit_sha"; exit 1 ;;
    esac

    porcelain="$(git status --porcelain)"
    if [ -n "$porcelain" ]; then
      echo "   unexpected working-tree changes (the tree must be clean):"
      printf '%s\n' "$porcelain" | sed 's/^/     /'
      exit 1
    fi
    echo "   working tree clean"
    REMOTE_A
      echo "[gate] A PASS  git integrity"
    else
      gate_fail "assertion A — git integrity"
    fi

    # B — pi has models. `pi --list-models` EXITS 0 while printing
    # "No models available", so never trust $?: assert on the output, and
    # reject that exact string, which is otherwise one non-empty line and would
    # sail through a naive non-empty check.
    echo "[gate] B pi --list-models is non-empty"
    if "${SSH[@]}" 'bash -s' <<'REMOTE_B'; then
    set -uo pipefail
    # `command -v` first: without it a missing pi prints one line of
    # "command not found" and a bare non-empty check calls that a pass.
    command -v pi >/dev/null 2>&1 || { echo "   pi is not on PATH"; exit 1; }
    out="$(pi --list-models 2>&1 || true)"
    n="$(printf '%s\n' "$out" | grep -c . || true)"
    if [ "${n:-0}" -eq 0 ]; then
      echo "   pi --list-models printed nothing"; exit 1
    fi
    if printf '%s' "$out" | grep -qi 'no models available'; then
      echo "   pi says: No models available — ~/.pi/agent/models.json did not load"; exit 1
    fi
    echo "   ${n} lines from pi --list-models"
    REMOTE_B
      echo "[gate] B PASS  pi model registry loaded"
    else
      gate_fail "assertion B — pi --list-models empty or 'No models available'"
    fi

    # C, D, E run as ONE script inside the sandbox. They all need the runtime
    # key, which lives in app/.env on the VM — keeping them there means the key
    # never crosses the wire and the gate exercises the sandbox's own egress.
    #
    # The remote process exit is transport evidence, not acceptance evidence.
    # B3-005 observed remote FAIL lines followed by host PASS lines, so the host
    # now requires one typed result marker and reconciles it with the complete
    # captured output and remote exit before any downstream PASS can print.
    echo "[gate] C roster ping   D non-zero cost   E runtime key limit"
    CDE_LOG="$(mktemp -t 'sssf-setup-cde.XXXXXX')"
    set +e
    "${SSH[@]}" 'bash -s' {{ quote(CONFIG) }} >"$CDE_LOG" 2>&1 <<'REMOTE_CDE'
    set -uo pipefail
    cd "$HOME/app" || { echo "   no ~/app on this VM"; exit 1; }
    command -v jq >/dev/null 2>&1 || { echo "   jq missing (it ships in the exeuntu image)"; exit 1; }

    # Runtime key, read exactly the way provision.sh reads it. NEVER echoed.
    KEY="$(grep -E '^[[:space:]]*(export[[:space:]]+)?OPENROUTER_API_KEY=' .env \
           | tail -n 1 | sed -E 's/^[^=]*=//; s/^["'"'"']//; s/["'"'"']$//' || true)"
    [ -n "$KEY" ] || { echo "   no OPENROUTER_API_KEY in app/.env — FILL did not inject the runtime key"; exit 1; }

    # ── C: ping every model in the ACTIVE roster ─────────────────────────────
    CFG="${1:-}"
    [ -n "$CFG" ] || CFG="${SSSF_CONFIG:-adws/adw_sssf_config/sssf.config.yaml}"
    [ -f "$CFG" ] || { echo "   missing ${CFG}"; exit 1; }
    MODELS="$(awk '/^[[:space:]]*model:[[:space:]]/ {print $2}' "$CFG" \
              | sed 's|^openrouter/||' | sort -u)"
    [ -n "$MODELS" ] || { echo "   parsed zero models out of ${CFG}"; exit 1; }

    roster_state=PASS
    for m in $MODELS; do
      body="$(printf '{"model":"%s","max_tokens":256,"provider":{"zdr":true,"data_collection":"deny"},"messages":[{"role":"user","content":"ping - respond with pong"}]}' "$m")"
      resp="$(curl -sS --max-time 180 https://openrouter.ai/api/v1/chat/completions \
                -H "Authorization: Bearer ${KEY}" \
                -H 'Content-Type: application/json' \
                -d "$body" || true)"
      text="$(printf '%s' "$resp" | jq -r '
        ((.choices[0].message.content // "") + (.choices[0].message.reasoning // ""))
      ' 2>/dev/null || true)"
      if [ -n "$text" ] && [ "$text" != "null" ]; then
        echo "   pass  ${m}"
      else
        err="$(printf '%s' "$resp" | jq -r '.error.message // .error // "no content and no error field"' 2>/dev/null || echo 'unparseable response')"
        if printf '%s' "$err" | grep -qi 'insufficient credits'; then
          echo "   CNO   ${m}: model evidence unavailable (insufficient credits)"
          [ "$roster_state" = FAIL ] || roster_state=CNO
        else
          echo "   FAIL  ${m}: ${err}"
          roster_state=FAIL
        fi
      fi
    done

    # ── D: pi actually REPORTS cost ──────────────────────────────────────────
    # A successful call must report non-zero cost, and the static registry must
    # carry rates. Unavailable live inference is CNO, never evidence of PASS.
    cost_state=PASS
    pi_raw="$(timeout 180 pi -p --mode json \
                 --provider openrouter --model deepseek/deepseek-v4-flash-0731 \
                 'Write one sentence about sandboxes.' 2>&1)"
    pi_rc=$?
    pi_cost="$(printf '%s' "$pi_raw" \
               | jq -s '[.. | objects | select(has("cost")) | .cost.total // 0] | max // 0' \
                 2>/dev/null || echo 0)"
    if [ "$pi_rc" -eq 0 ] && awk -v c="$pi_cost" 'BEGIN { exit !(c > 0) }'; then
      echo "   pi reports cost \$${pi_cost} on a live call"
    else
      echo "   CNO   live pi cost unavailable; no successful non-zero-cost call"
      cost_state=CNO
    fi

    MJ="$HOME/.pi/agent/models.json"
    if [ -f "$MJ" ] && jq -e '[.providers[].models[] | (.cost.input // 0)] | (length > 0) and all(. > 0)' "$MJ" >/dev/null 2>&1; then
      echo "   rate table present: every model has a non-zero input cost"
    else
      echo "   FAIL  models.json is missing rates"
      cost_state=FAIL
    fi

    # ── E: runtime key limit/usage evidence ──────────────────────────────────
    credit_state=PASS
    kj="$(curl -sS --max-time 60 https://openrouter.ai/api/v1/key -H "Authorization: Bearer ${KEY}" 2>/dev/null || true)"
    if printf '%s' "$kj" | jq -e '.data | type == "object"' >/dev/null 2>&1; then
      printf '%s' "$kj" | jq -r '
        .data as $d
        | "   limit     " + (if $d.limit == null then "uncapped" else ("$" + ($d.limit|tostring)) end),
          "   used      $" + (($d.usage // 0)|tostring),
          "   remaining " + (if $d.limit == null then "uncapped" else ("$" + (($d.limit - ($d.usage // 0))|tostring)) end)
      '
    else
      echo "   CNO   runtime key limit/usage unavailable"
      credit_state=CNO
    fi

    printf 'SSSF_CDE_RESULT {"roster":"%s","cost":"%s","credit":"%s"}\n' \
      "$roster_state" "$cost_state" "$credit_state"
    if [ "$roster_state" = FAIL ] || [ "$cost_state" = FAIL ] || [ "$credit_state" = FAIL ]; then
      exit 20
    fi
    if [ "$roster_state" = CNO ] || [ "$cost_state" = CNO ] || [ "$credit_state" = CNO ]; then
      exit 21
    fi
    exit 0
    REMOTE_CDE
    CDE_REMOTE_RC=$?
    set -e

    cat "$CDE_LOG"
    set +e
    python tools/setup_cde_acceptance.py --remote-exit "$CDE_REMOTE_RC" "$CDE_LOG"
    CDE_ACCEPT_RC=$?
    set -e
    rm -f "$CDE_LOG"

    case "$CDE_ACCEPT_RC" in
      0)
        echo "[gate] C PASS  every roster model answered"
        echo "[gate] D PASS  non-zero live cost and loaded rate table"
        echo "[gate] E PASS  runtime key limit/usage reported"
        ;;
      1) gate_fail "assertions C/D/E — typed remote evidence contains a failure" ;;
      3) gate_fail "assertions C/D/E — CNO/HOLD; required remote evidence unavailable" ;;
      *) gate_fail "assertions C/D/E — acceptance helper error ${CDE_ACCEPT_RC}" ;;
    esac

    echo ""
    echo "[setup] GATE PASSED — {{RUN_ID}} is healthy on ${HOST}"
    echo "[setup] next: just sbx lifecycle observe {{RUN_ID}}"
