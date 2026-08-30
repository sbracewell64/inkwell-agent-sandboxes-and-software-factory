# just/sandbox/lifecycle/mod.just — the six phases, in order.
#
# create -> fill -> setup -> execute -> observe -> teardown. `just sbx mount`
# chains the first three plus observe; these exist for when you need one on its
# own — a re-run of setup after fixing a gate failure, a second execute, a
# teardown you decided on deliberately.
#
# `authority` sits beside them rather than in the chain: it is the deterministic
# control #36 LAW_1 watched-red run over the three seams that perform an effect,
# and it touches nothing.
#
# A module inherits nothing, so the three settings are repeated here with one
# more `..` than the parent. The phase files are `import`ed, so they share this
# scope and define no settings and no top-level variables of their own — six
# files in one scope means a duplicate name is a hard error.
set working-directory := '../../..'
set positional-arguments
set dotenv-load

import 'authority.just'
import 'create.just'
import 'fill.just'
import 'setup.just'
import 'execute.just'
import 'observe.just'
import 'teardown.just'

# list the lifecycle phases
default:
    @just --list sbx::lifecycle
