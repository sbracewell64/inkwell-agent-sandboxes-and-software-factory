[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("bootstrap", "lifecycle", "teardown")]
    [string]$Phase,

    [Parameter(Mandatory = $true)]
    [string]$ProofPath,

    [Parameter(Mandatory = $true)]
    [string]$EvidencePath,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedSha,

    [string]$RunId = "",
    [string]$ConfigSource = "E:\SSSF\.env",
    [string]$SourceRepo = "https://github.com/sbracewell64/inkwell-agent-sandboxes-and-software-factory.git",
    [string]$Branch = "increment/b3-005-fresh-windows-clone-proof"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

if ($ExpectedSha -notmatch "^[0-9a-f]{40}$") {
    throw "ExpectedSha must be an exact lowercase 40-character SHA"
}
if ($Phase -ne "bootstrap" -and [string]::IsNullOrWhiteSpace($RunId)) {
    throw "RunId is required for lifecycle and teardown"
}

Add-Type -TypeDefinition @"
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;

public static class NativeUserEnvironment
{
    private const UInt32 TOKEN_QUERY = 0x0008;
    private const UInt32 TOKEN_DUPLICATE = 0x0002;

    [DllImport("advapi32.dll", SetLastError = true)]
    private static extern bool OpenProcessToken(
        IntPtr processHandle,
        UInt32 desiredAccess,
        out IntPtr tokenHandle);

    [DllImport("userenv.dll", SetLastError = true)]
    private static extern bool CreateEnvironmentBlock(
        out IntPtr environment,
        IntPtr token,
        bool inherit);

    [DllImport("userenv.dll", SetLastError = true)]
    private static extern bool DestroyEnvironmentBlock(IntPtr environment);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);

    public static Dictionary<string, string> CreateCurrentUserBlock()
    {
        IntPtr token;
        if (!OpenProcessToken(Process.GetCurrentProcess().Handle,
                              TOKEN_QUERY | TOKEN_DUPLICATE,
                              out token))
            throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());

        IntPtr block = IntPtr.Zero;
        try {
            // inherit=false is load-bearing: no variable from the WSL worker or
            // this PowerShell parent is inherited into the proof process.
            if (!CreateEnvironmentBlock(out block, token, false))
                throw new System.ComponentModel.Win32Exception(Marshal.GetLastWin32Error());

            var result = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            IntPtr cursor = block;
            while (true) {
                string entry = Marshal.PtrToStringUni(cursor);
                if (String.IsNullOrEmpty(entry)) break;
                cursor = IntPtr.Add(cursor, (entry.Length + 1) * 2);
                int split = entry.IndexOf('=', 1);
                if (split > 0)
                    result[entry.Substring(0, split)] = entry.Substring(split + 1);
            }
            return result;
        }
        finally {
            if (block != IntPtr.Zero) DestroyEnvironmentBlock(block);
            CloseHandle(token);
        }
    }
}
"@

function Write-Utf8NoBom([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText(
        $Path,
        $Text,
        (New-Object System.Text.UTF8Encoding($false)))
}

function Format-RegistryEnvironment([Microsoft.Win32.RegistryKey]$Key, [string]$Scope) {
    $lines = New-Object System.Collections.Generic.List[string]
    $lines.Add("[$Scope]")
    if ($null -eq $Key) {
        $lines.Add("<KEY-UNAVAILABLE>")
        return $lines
    }
    foreach ($name in @($Key.GetValueNames() | Sort-Object)) {
        $kind = $Key.GetValueKind($name).ToString()
        $value = $Key.GetValue($name, $null, [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
        $lines.Add("$name|$kind|$value")
    }
    return $lines
}

function Capture-PersistentEnvironment([string]$Path) {
    $machine = [Microsoft.Win32.Registry]::LocalMachine.OpenSubKey(
        "SYSTEM\CurrentControlSet\Control\Session Manager\Environment")
    $user = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Environment")
    try {
        $lines = New-Object System.Collections.Generic.List[string]
        $lines.Add("captured_utc=$([DateTime]::UtcNow.ToString('o'))")
        $lines.AddRange([string[]](Format-RegistryEnvironment $machine "HKLM"))
        $lines.AddRange([string[]](Format-RegistryEnvironment $user "HKCU"))
        Write-Utf8NoBom $Path (($lines -join "`r`n") + "`r`n")
    }
    finally {
        if ($null -ne $machine) { $machine.Dispose() }
        if ($null -ne $user) { $user.Dispose() }
    }
}

function Stage-ProvisioningConfig([string]$Source, [string]$Destination) {
    if (-not (Test-Path -LiteralPath $Source -PathType Leaf)) {
        throw "approved host config source is unavailable: $Source"
    }
    $matches = @(
        [System.IO.File]::ReadAllLines($Source) |
            Where-Object { $_ -match '^\s*OPENROUTER_PROVISIONING_KEY=' })
    if ($matches.Count -ne 1) {
        throw "approved host config must contain exactly one OPENROUTER_PROVISIONING_KEY entry"
    }
    Write-Utf8NoBom $Destination ($matches[0] + "`r`n")
}

$proofFull = [System.IO.Path]::GetFullPath($ProofPath)
$evidenceFull = [System.IO.Path]::GetFullPath($EvidencePath)

if ($Phase -eq "bootstrap") {
    if (Test-Path -LiteralPath $proofFull) {
        throw "fresh proof path already exists: $proofFull"
    }
    if (Test-Path -LiteralPath $evidenceFull) {
        throw "fresh evidence path already exists: $evidenceFull"
    }
    [System.IO.Directory]::CreateDirectory($evidenceFull) | Out-Null
} else {
    if (-not (Test-Path -LiteralPath $proofFull -PathType Container)) {
        throw "proof path unavailable: $proofFull"
    }
    if (-not (Test-Path -LiteralPath $evidenceFull -PathType Container)) {
        throw "evidence path unavailable: $evidenceFull"
    }
}

$phaseEvidence = Join-Path $evidenceFull $Phase
if (Test-Path -LiteralPath $phaseEvidence) {
    throw "phase evidence already exists; refusing overwrite: $phaseEvidence"
}
[System.IO.Directory]::CreateDirectory($phaseEvidence) | Out-Null

$nativeEnvironment = [NativeUserEnvironment]::CreateCurrentUserBlock()
$nativeLines = New-Object System.Collections.Generic.List[string]
$nativeLines.Add("created_by=CreateEnvironmentBlock(current-user-token, inherit=false)")
$nativeLines.Add("created_utc=$([DateTime]::UtcNow.ToString('o'))")
foreach ($entry in @($nativeEnvironment.GetEnumerator() | Sort-Object Key)) {
    $nativeLines.Add("$($entry.Key)=$($entry.Value)")
}
Write-Utf8NoBom (Join-Path $phaseEvidence "native-process-environment.txt") (($nativeLines -join "`r`n") + "`r`n")
Capture-PersistentEnvironment (Join-Path $phaseEvidence "persistent-environment-before.txt")

$launcherHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLowerInvariant()
$processLines = @(
    "phase=$Phase",
    "launcher=$PSCommandPath",
    "launcher_sha256=$launcherHash",
    "parent_pid=$PID",
    "windows_identity=$([System.Security.Principal.WindowsIdentity]::GetCurrent().Name)",
    "proof_path=$proofFull",
    "evidence_path=$evidenceFull",
    "source_repo=$SourceRepo",
    "branch=$Branch",
    "expected_sha=$ExpectedSha",
    "run_id=$RunId",
    "config_source=$ConfigSource",
    "child_environment=CreateEnvironmentBlock(current-user-token, inherit=false)",
    "child_executable=$($nativeEnvironment['SystemRoot'])\System32\cmd.exe",
    "child_working_directory=$([System.IO.Path]::GetDirectoryName($proofFull))"
)
Write-Utf8NoBom (Join-Path $phaseEvidence "process-creation.txt") (($processLines -join "`r`n") + "`r`n")

$batchPath = Join-Path $phaseEvidence "proof-driver.cmd"
$commonHeader = @"
@echo off
setlocal EnableExtensions DisableDelayedExpansion
set "PROOF=$proofFull"
set "EVIDENCE=$phaseEvidence"
set "EXPECTED=$ExpectedSha"
set "RUN_ID=$RunId"
set "REPO=$SourceRepo"
set "BRANCH=$Branch"
echo phase=$Phase
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
"@

if ($Phase -eq "bootstrap") {
    $body = @"
$commonHeader
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
"@
} elseif ($Phase -eq "lifecycle") {
    Stage-ProvisioningConfig $ConfigSource (Join-Path $proofFull ".env")
    $body = @"
$commonHeader
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
"@
} else {
    $body = @"
$commonHeader
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
"@
}

Write-Utf8NoBom $batchPath $body

$cmd = Join-Path $nativeEnvironment["SystemRoot"] "System32\cmd.exe"
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $cmd
$psi.Arguments = "/d /s /c `"`"$batchPath`"`""
$psi.WorkingDirectory = [System.IO.Path]::GetDirectoryName($proofFull)
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables.Clear()
foreach ($entry in $nativeEnvironment.GetEnumerator()) {
    $psi.EnvironmentVariables[$entry.Key] = $entry.Value
}

$process = New-Object System.Diagnostics.Process
$process.StartInfo = $psi
if (-not $process.Start()) { throw "could not start native cmd proof process" }
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$stdout = $stdoutTask.Result
$stderr = $stderrTask.Result
Write-Utf8NoBom (Join-Path $phaseEvidence "stdout.txt") $stdout
Write-Utf8NoBom (Join-Path $phaseEvidence "stderr.txt") $stderr
Write-Utf8NoBom (Join-Path $phaseEvidence "exit-code.txt") ("$($process.ExitCode)`r`n")
Capture-PersistentEnvironment (Join-Path $phaseEvidence "persistent-environment-after.txt")

$manifestLines = New-Object System.Collections.Generic.List[string]
foreach ($file in @(Get-ChildItem -LiteralPath $phaseEvidence -File | Sort-Object Name)) {
    if ($file.Name -eq "sha256-manifest.txt") { continue }
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash.ToLowerInvariant()
    $manifestLines.Add("$hash  $($file.Name)")
}
Write-Utf8NoBom (Join-Path $phaseEvidence "sha256-manifest.txt") (($manifestLines -join "`r`n") + "`r`n")

if ($process.ExitCode -ne 0) {
    throw "native proof phase '$Phase' failed with exit code $($process.ExitCode); evidence retained at $phaseEvidence"
}

Write-Output "B3-005 native proof phase ${Phase}: PASS"
Write-Output "evidence: $phaseEvidence"
