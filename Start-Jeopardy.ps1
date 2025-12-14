[CmdletBinding()]
param(
    [int]$Port = 5000,
    [switch]$Install,
    [switch]$OpenBrowser,
    [string]$HostUrl = "http://127.0.0.1",
    [string]$PublicJoinUrl = "https://jeopardy.haydd.com"
)

$ErrorActionPreference = 'Stop'

function Write-Info([string]$Message) {
    Write-Host "[Jeopardy] $Message" -ForegroundColor Cyan
}

try {
    $repoRoot = $PSScriptRoot
    if (-not $repoRoot) {
        $repoRoot = (Get-Location).Path
    }

    Set-Location $repoRoot

    # Prefer workspace venv; create if missing
    $venvPython = Join-Path $repoRoot '.venv\Scripts\python.exe'
    if (-not (Test-Path $venvPython)) {
        Write-Info "Creating virtual environment at .venv (first run)"
        python -m venv .venv
    }

    # Activate venv (best-effort; not strictly required if we call venv python explicitly)
    $activate = Join-Path $repoRoot '.venv\Scripts\Activate.ps1'
    if (Test-Path $activate) {
        try {
            . $activate
        } catch {
            Write-Host "[Jeopardy] NOTE: Could not activate venv via Activate.ps1 (ExecutionPolicy?)." -ForegroundColor Yellow
            Write-Host "[Jeopardy] You can allow scripts with: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor Yellow
        }
    }

    if ($Install) {
        Write-Info "Installing/updating Python dependencies"
        & $venvPython -m pip install --upgrade pip
        & $venvPython -m pip install -r (Join-Path $repoRoot 'requirements.txt')
    }

    $env:PORT = "$Port"
    if ($PublicJoinUrl) {
        $env:PUBLIC_JOIN_URL = $PublicJoinUrl
    }

    if ($OpenBrowser) {
        $admin = "$HostUrl`:$Port/admin"
        $board = "$HostUrl`:$Port/board"
        $player = "$HostUrl`:$Port/player?name=Player"
        Write-Info "Opening: $admin"
        Start-Process $admin | Out-Null
        Start-Sleep -Milliseconds 250
        Write-Info "Opening: $board"
        Start-Process $board | Out-Null
        Start-Sleep -Milliseconds 250
        Write-Info "Opening: $player"
        Start-Process $player | Out-Null
    }

    Write-Info "Starting Jeopardy server on port $Port"
    Write-Info "Admin:  $HostUrl`:$Port/admin"
    Write-Info "Board:  $HostUrl`:$Port/board"
    Write-Info "Player: $HostUrl`:$Port/player?name=YourName"

    & $venvPython (Join-Path $repoRoot 'app.py')
}
catch {
    Write-Host "[Jeopardy] Startup failed: $($_.Exception.Message)" -ForegroundColor Red
    throw
}
