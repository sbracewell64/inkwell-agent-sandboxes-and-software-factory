@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PROOF=E:\SSSF-B3-005-PROOF-20260815-154222"
set "EVIDENCE=E:\SSSF-B3-005-EVIDENCE-20260815-154222\teardown"
set "EXPECTED=efd84ab02fee4cb4c8e1e116616e039ba84a0546"
set "RUN_ID=b3-005-proof-20260815-b30005"
set "REPO=https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
set "BRANCH=increment/b3-005-fresh-windows-clone-proof"
set "CONFIG_SOURCE=E:\SSSF\.env"
echo phase=teardown
echo started_utc=%DATE% %TIME%
echo proof_path=%PROOF%
echo evidence_path=%EVIDENCE%
echo expected_sha=%EXPECTED%
echo process_architecture=%PROCESSOR_ARCHITECTURE%
echo comspec=%COMSPEC%
echo prebootstrap_path=%PATH%
echo --- pre-bootstrap executable resolution ---
where git
echo where_git_exit=%ERRORLEVEL%
where just
echo where_just_exit=%ERRORLEVEL%
where ssh
echo where_ssh_exit=%ERRORLEVEL%
where sh
echo where_sh_exit=%ERRORLEVEL%
if not errorlevel 1 exit /b 41
where cygpath
echo where_cygpath_exit=%ERRORLEVEL%
if not errorlevel 1 exit /b 42
where zsh
echo where_zsh_exit=%ERRORLEVEL%
if not errorlevel 1 exit /b 43
echo ;%PATH%; | %SystemRoot%\System32\findstr.exe /i /l /c:";C:\Program Files\Git\bin;" >nul
if not errorlevel 1 exit /b 44
echo ;%PATH%; | %SystemRoot%\System32\findstr.exe /i /l /c:";C:\Program Files\Git\usr\bin;" >nul
if not errorlevel 1 exit /b 45
echo negative_control_git_bin_absent=PASS
echo negative_control_git_usr_bin_absent=PASS
cd /d "%PROOF%"
for /f %%S in ('git rev-parse HEAD') do set "ACTUAL=%%S"
if /i not "%EXPECTED%"=="%ACTUAL%" exit /b 81
call bin\sssf-windows.cmd --sandbox
if errorlevel 1 exit /b 82
echo --- teardown through project lifecycle ---
call just sbx lifecycle teardown "%RUN_ID%"
if errorlevel 1 exit /b 83
echo --- post-teardown controls ---
if exist ".sandbox\runs\%RUN_ID%.key" exit /b 84
call ssh exe.dev ls --json > "%EVIDENCE%\fleet-after.json"
if errorlevel 1 exit /b 85
python -c "import json,sys; d=json.load(open(r'%EVIDENCE%\fleet-after.json')); sys.exit(1 if r'%RUN_ID%' in {v.get('vm_name') for v in d.get('vms',[])} else 0)"
if errorlevel 1 exit /b 86
sandbox_mount\host\run_record.py get "%RUN_ID%" closed_at
if errorlevel 1 exit /b 87
git status --porcelain=v2 --branch
git diff --exit-code
if errorlevel 1 exit /b 88
echo teardown_phase=PASS
exit /b 0
