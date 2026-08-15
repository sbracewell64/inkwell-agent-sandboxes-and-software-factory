@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PROOF=E:\SSSF-B3-005-PROOF-20260815-154222"
set "EVIDENCE=E:\SSSF-B3-005-EVIDENCE-20260815-154222\lifecycle"
set "EXPECTED=efd84ab02fee4cb4c8e1e116616e039ba84a0546"
set "RUN_ID=b3-005-proof-20260815-b30005"
set "REPO=https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
set "BRANCH=increment/b3-005-fresh-windows-clone-proof"
set "CONFIG_SOURCE=E:\SSSF\.env"
echo phase=lifecycle
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
if /i not "%EXPECTED%"=="%ACTUAL%" exit /b 61
git status --porcelain=v2 --branch
git diff --exit-code
if errorlevel 1 exit /b 62
git check-ignore -v .env
if errorlevel 1 exit /b 63
call bin\sssf-windows.cmd --sandbox
if errorlevel 1 exit /b 64
echo --- lifecycle create ---
call just sbx lifecycle create "%RUN_ID%"
if errorlevel 1 exit /b 65
echo --- lifecycle fill ---
call just sbx lifecycle fill "%RUN_ID%"
if errorlevel 1 exit /b 66
echo --- lifecycle setup ---
call just sbx lifecycle setup "%RUN_ID%"
if errorlevel 1 exit /b 67
echo --- lifecycle observe ---
call just sbx lifecycle observe "%RUN_ID%"
if errorlevel 1 exit /b 68
echo --- independent guest source and cleanliness ---
call just sbx run cmd "%RUN_ID%" "printf 'origin=' && git remote get-url origin && printf 'HEAD=' && git rev-parse HEAD && git status --porcelain=v2 --branch"
if errorlevel 1 exit /b 69
echo --- guest sqlite-free observability ---
call just sbx run cmd "%RUN_ID%" "command -v sqlite3 || true; python docs/validation/check_obs_query.py --require-no-external-sqlite3"
if errorlevel 1 exit /b 70
echo --- pre-teardown negative controls ---
if not exist ".sandbox\runs\%RUN_ID%.key" exit /b 71
call ssh exe.dev ls "%RUN_ID%" --json
if errorlevel 1 exit /b 72
git status --porcelain=v2 --branch
git diff --exit-code
if errorlevel 1 exit /b 73
echo lifecycle_phase=PASS
exit /b 0
