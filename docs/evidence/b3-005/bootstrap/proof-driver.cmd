@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PROOF=E:\SSSF-B3-005-PROOF-20260815-154222"
set "EVIDENCE=E:\SSSF-B3-005-EVIDENCE-20260815-154222\bootstrap"
set "EXPECTED=efd84ab02fee4cb4c8e1e116616e039ba84a0546"
set "RUN_ID="
set "REPO=https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git"
set "BRANCH=increment/b3-005-fresh-windows-clone-proof"
set "CONFIG_SOURCE=E:\SSSF\.env"
echo phase=bootstrap
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
echo exact_clone_command=git clone --single-branch --branch %BRANCH% %REPO% %PROOF%
git clone --single-branch --branch "%BRANCH%" "%REPO%" "%PROOF%"
if errorlevel 1 exit /b 50
cd /d "%PROOF%"
echo --- exact clone identity ---
git rev-parse HEAD
git status --porcelain=v2 --branch
git remote -v
for /f %%S in ('git rev-parse HEAD') do set "ACTUAL=%%S"
if /i not "%EXPECTED%"=="%ACTUAL%" exit /b 51
echo --- root front doors before bootstrap ---
call just
if errorlevel 1 exit /b 52
call just local
if errorlevel 1 exit /b 53
echo --- approved ignored host configuration ---
%SystemRoot%\System32\findstr.exe /b /c:"OPENROUTER_PROVISIONING_KEY=" "%CONFIG_SOURCE%" > "%PROOF%\.env"
if errorlevel 1 exit /b 531
git check-ignore -v .env
if errorlevel 1 exit /b 532
echo staged_config_name=OPENROUTER_PROVISIONING_KEY
echo staged_config_value=REDACTED
echo --- repository bootstrap and composed doctor ---
call bin\sssf-windows.cmd --sandbox
if errorlevel 1 exit /b 54
echo postbootstrap_path=%PATH%
where sh
if errorlevel 1 exit /b 55
where cygpath
if errorlevel 1 exit /b 56
where ssh
if errorlevel 1 exit /b 57
echo --- B3-004 sqlite-free observability ---
where sqlite3
echo where_sqlite3_exit=%ERRORLEVEL%
if not errorlevel 1 exit /b 58
python docs\validation\check_obs_query.py --require-no-external-sqlite3
if errorlevel 1 exit /b 59
echo --- proof clone tracked state ---
git status --porcelain=v2 --branch
git diff --exit-code
if errorlevel 1 exit /b 60
echo bootstrap_phase=PASS
exit /b 0
