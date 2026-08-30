# just/sandbox/lifecycle/authority.just — the SDLC-L1 effect-seam authority controls.
#
# IMPORTED by lifecycle/mod.just, so no `set` lines and no top-level variables:
# the phase files share one scope and a duplicate name across them is a hard
# error.
#
# Three recipes in this directory perform an irreversible, spending, or exposing
# effect — teardown destroys a VM, create mints a spending runtime key, observe
# publishes a sandbox anonymously. Under control #36 LAW_1 each runs behind a
# one-use capability bound to this exact repository, head and target, and a
# repository landing authorization is never reusable as that authority.
#
# This recipe runs the watched reds that prove it, in process. It makes NO
# exe.dev, OpenRouter, ssh, or network call and creates nothing: it is safe to
# run at any time, on any checkout, with no run in flight.

# run the control #36 LAW_1 watched-red controls over the three live effect seams
authority:
    #!/usr/bin/env bash
    set -euo pipefail
    python3 -m adws.adw_modules.sandbox_provider controls
