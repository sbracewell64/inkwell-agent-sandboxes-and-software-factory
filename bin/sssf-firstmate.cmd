@echo off
setlocal EnableExtensions DisableDelayedExpansion

rem SSSF's canonical Windows front door. It is deliberately transport-only:
rem validate E:\SSSF, carry its non-secret identity into Firstmate, and hand off
rem to Firstmate's existing primary launcher. Firstmate remains the owner of
rem supervision, admission, harness selection, and all work decisions.
set "SSSF_LAUNCH_MODE=interactive"
if "%~1"=="" goto sssf_arguments_ok
if /i "%~1"=="--detach" goto sssf_detach_argument
if /i "%~1"=="--print-menu" goto sssf_print_menu_argument
goto sssf_bad_arguments
:sssf_detach_argument
if not "%~2"=="" goto sssf_bad_arguments
set "SSSF_LAUNCH_MODE=detach"
goto sssf_arguments_ok
:sssf_print_menu_argument
if not "%~2"=="" goto sssf_bad_arguments
set "SSSF_LAUNCH_MODE=print-menu"
goto sssf_arguments_ok
:sssf_bad_arguments
>&2 echo Usage: sssf-firstmate.cmd [--detach^|--print-menu]
>&2 echo Unknown or extra command-line values were refused.
endlocal & exit /b 2
:sssf_arguments_ok
set "SSSF_ROOT=E:\SSSF"
if not exist "%SSSF_ROOT%\." (
    >&2 echo SSSF front door could not find the canonical repository at E:\SSSF.
    >&2 echo Mount or clone the operator-owned SSSF checkout there, then retry.
    endlocal & exit /b 1
)

if defined SSSF_WSL_EXE (
    set "SSSF_WSL_COMMAND=%SSSF_WSL_EXE%"
) else (
    set "SSSF_WSL_COMMAND=%SystemRoot%\System32\wsl.exe"
)
if not exist "%SSSF_WSL_COMMAND%" (
    >&2 echo SSSF front door could not find WSL at "%SSSF_WSL_COMMAND%".
    >&2 echo Install WSL, then retry.
    endlocal & exit /b 127
)
"%SSSF_WSL_COMMAND%" --exec /bin/sh -c "test -x /bin/bash || { echo 'SSSF front door could not find Bash at /bin/bash.'; echo 'Install Bash in the WSL distribution, then retry.'; exit 127; }"
set "SSSF_DEPENDENCY_EXIT=%ERRORLEVEL%"
if not "%SSSF_DEPENDENCY_EXIT%"=="0" (
    >&2 echo.
    >&2 echo SSSF front door dependency preflight failed. Exit status: %SSSF_DEPENDENCY_EXIT%.
    endlocal & exit /b %SSSF_DEPENDENCY_EXIT%
)
if defined SSSF_HERDR_LAB_SESSION (
    if defined WSLENV (
        set "WSLENV=SSSF_HERDR_LAB_SESSION:%WSLENV%"
    ) else (
        set "WSLENV=SSSF_HERDR_LAB_SESSION"
    )
)

rem The inline WSL handoff keeps this single tracked file runnable from any
rem caller cwd and avoids putting a private checkout path into argv. The WSL
rem side resolves Firstmate from its normal home, not from the caller's cwd.
"%SSSF_WSL_COMMAND%" --cd "%SSSF_ROOT%" --exec /bin/bash -c "set -eu; command -v git >/dev/null 2>&1 || { echo 'SSSF front door could not find Git in WSL.'; echo 'Install Git in the WSL distribution, then retry.'; exit 127; }; command -v grep >/dev/null 2>&1 || { echo 'SSSF front door could not find grep in WSL.'; echo 'Install grep in the WSL distribution, then retry.'; exit 127; }; lab=${SSSF_HERDR_LAB_SESSION:-}; case $lab in '') ;; fm-lab-[A-Za-z0-9_-]*) case $lab in *[!A-Za-z0-9_-]*) echo 'SSSF front door received an invalid named Herdr lab session.'; exit 2;; *) export HERDR_SESSION=$lab; unset SSSF_HERDR_LAB_SESSION;; esac ;; *) echo 'SSSF front door requires a named non-default Herdr lab session.'; exit 2;; esac; root=$(pwd -P); case $root in /mnt/e/SSSF) ;; *) echo 'SSSF front door reached the wrong WSL root: '$root; exit 1;; esac; test -e .git || { echo 'SSSF front door found no Git checkout at E:\SSSF.'; exit 1; }; test -r AGENTS.md || { echo 'SSSF front door found no AGENTS.md at E:\SSSF.'; exit 1; }; test -r bin/sssf-windows.cmd || { echo 'SSSF front door found no tracked Windows entrypoint at E:\SSSF.'; exit 1; }; origin=$(git config --get remote.origin.url || true); case $origin in https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git|git@github.com:sbracewell64/inkwell-agent-sandboxes-and-software-factory.git) ;; *) echo 'SSSF front door found a checkout with a non-canonical origin.'; exit 1;; esac; for directory in $HOME/bin $HOME/.local/bin; do case :$PATH: in *:$directory:*) ;; *) test -d $directory && PATH=$directory:$PATH ;; esac; done; export PATH; fm=${SSSF_FIRSTMATE_ROOT:-$HOME/kun-agent-workspace}; case $fm in *[!A-Za-z0-9_./-]*) echo 'SSSF front door found an invalid Firstmate root configuration.'; exit 1;; esac; test -x $fm/bin/fm-launch.sh || { echo 'SSSF front door could not find executable Firstmate bin/fm-launch.sh.'; exit 1; }; test -x $fm/bin/fm-admission.sh || { echo 'SSSF front door could not find executable Firstmate bin/fm-admission.sh.'; exit 1; }; test -x $fm/bin/fm-session-start.sh || { echo 'SSSF front door could not find executable Firstmate bin/fm-session-start.sh.'; exit 1; }; test -r $fm/data/projects.md || { echo 'SSSF front door could not read the Firstmate project registry.'; exit 1; }; grep -Eq '(^|:) *- sssf \[' $fm/data/projects.md || { echo 'SSSF is not registered in the Firstmate project registry.'; exit 1; }; printf 'SSSF front door: project=sssf repository=sbracewell64/inkwell-agent-sandboxes-and-software-factory root=E:\\SSSF handoff=firstmate\n'; export SSSF_FRONT_DOOR_PROJECT=sssf SSSF_FRONT_DOOR_REPOSITORY=sbracewell64/inkwell-agent-sandboxes-and-software-factory SSSF_FRONT_DOOR_ROOT=E:\\SSSF SSSF_FRONT_DOOR_ROOT_WSL=$root SSSF_FRONT_DOOR_HANDOFF=firstmate; mode=%SSSF_LAUNCH_MODE%; case $mode in interactive) exec $fm/bin/fm-launch.sh ;; detach) exec $fm/bin/fm-launch.sh --entry claude --detach ;; print-menu) exec $fm/bin/fm-launch.sh --print-menu ;; *) echo 'SSSF front door found an invalid launch mode configuration.'; exit 2;; esac"
set "SSSF_EXIT=%ERRORLEVEL%"
if not "%SSSF_EXIT%"=="0" (
    >&2 echo.
    >&2 echo SSSF front door could not enter Firstmate. Exit status: %SSSF_EXIT%.
)
endlocal & exit /b %SSSF_EXIT%
