<#
Simple tunnel controller script for Windows (PowerShell)
Usage:
  .\tunnel.ps1 start [-StartApp]
  .\tunnel.ps1 stop
  .\tunnel.ps1 status

- Starts/stops the `jeopardy-tunnel` created with `cloudflared tunnel create`.
- Saves PID files to `%USERPROFILE%\.cloudflared\` so `stop` can find processes.
- Optionally starts the app (python app.py) when using `-StartApp` with `start`.
#>
param(
    [Parameter(Mandatory=$true, Position=0)]
    [ValidateSet('start','stop','status')]
    [string]
    $Action,

    [switch]
    $StartApp,

    [switch]
    $StartTunnel = $true,

    [int]
    $Port = 5000,

    [switch]
    $Install,

    [switch]
    $OpenBrowser,

    [string]
    $HostUrl = 'http://127.0.0.1',

    [string]
    $PublicJoinUrl = 'https://jeopardy.haydd.com',

    [string]
    $TunnelName = 'jeopardy-tunnel'
)

$ErrorActionPreference = 'Stop'

function Write-Info([string]$Message) {
    Write-Host "[Jeopardy] $Message" -ForegroundColor Cyan
}

function Get-RepoRoot {
    # Prefer the folder containing this script
    if ($PSScriptRoot) { return $PSScriptRoot }
    return (Get-Location).Path
}

function Get-VenvPython([string]$RepoRoot) {
    return (Join-Path $RepoRoot '.venv\Scripts\python.exe')
}

function Ensure-Venv([string]$RepoRoot) {
    $venvPython = Get-VenvPython -RepoRoot $RepoRoot
    if (-not (Test-Path $venvPython)) {
        Write-Info "Creating virtual environment at .venv (first run)"
        python -m venv (Join-Path $RepoRoot '.venv')
    }
    return $venvPython
}

function Install-Dependencies([string]$PythonExe, [string]$RepoRoot) {
    Write-Info "Installing/updating Python dependencies"
    & $PythonExe -m pip install --upgrade pip
    & $PythonExe -m pip install -r (Join-Path $RepoRoot 'requirements.txt')
}

function Start-JeopardyApp([string]$RepoRoot, [int]$Port, [switch]$Install) {
    $pythonExe = Ensure-Venv -RepoRoot $RepoRoot
    if ($Install) {
        Install-Dependencies -PythonExe $pythonExe -RepoRoot $RepoRoot
    }

    $env:PORT = "$Port"
    if ($PublicJoinUrl) {
        $env:PUBLIC_JOIN_URL = $PublicJoinUrl
    }
    Write-Info "Starting app (PORT=$Port)"
    $appProc = Start-Process -FilePath $pythonExe -ArgumentList (Join-Path $RepoRoot 'app.py') -WorkingDirectory $RepoRoot -PassThru -WindowStyle Hidden
    return $appProc
}

function Get-CloudflaredPath {
    $cmd = Get-Command cloudflared -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Path }
    # Fallback - common install location
    $fallback = 'C:\Program Files (x86)\cloudflared\cloudflared.exe'
    if (Test-Path $fallback) { return $fallback }
    return $null
}


$repoRoot = Get-RepoRoot
Set-Location $repoRoot

$cloudflared = Get-CloudflaredPath

$stateDir = Join-Path $env:USERPROFILE '.cloudflared'
if (-not (Test-Path $stateDir)) { New-Item -ItemType Directory -Path $stateDir | Out-Null }
$tunnelProcessIdFile = Join-Path $stateDir 'jeopardy-tunnel.pid'
$appProcessIdFile = Join-Path $stateDir 'jeopardy-app.pid'

switch ($Action) {
    'start' {
        if ($StartTunnel) {
            if (-not $cloudflared) {
                Write-Error "cloudflared not found. Install it or add it to PATH and try again."
                exit 1
            }

            if (Test-Path $tunnelProcessIdFile) {
                $existing = (Get-Content $tunnelProcessIdFile -ErrorAction SilentlyContinue)
                if ($existing -and (Get-Process -Id $existing -ErrorAction SilentlyContinue)) {
                    Write-Output "Tunnel already running (PID $existing)."
                } else {
                    Remove-Item $tunnelProcessIdFile -Force -ErrorAction SilentlyContinue
                }
            }

            Write-Output "Starting cloudflared tunnel '$TunnelName'..."
            $proc = Start-Process -FilePath $cloudflared -ArgumentList @('tunnel','run', $TunnelName) -WorkingDirectory $repoRoot -PassThru -WindowStyle Hidden
            $proc.Id | Out-File -FilePath $tunnelProcessIdFile -Encoding ascii
            Write-Output "Started cloudflared (PID $($proc.Id)). PID file: $tunnelProcessIdFile"
        }

        if ($StartApp) {
            if (Test-Path $appProcessIdFile) {
                $existingApp = (Get-Content $appProcessIdFile -ErrorAction SilentlyContinue)
                if ($existingApp -and (Get-Process -Id $existingApp -ErrorAction SilentlyContinue)) {
                    Write-Output "App already running (PID $existingApp)."
                } else {
                    Remove-Item $appProcessIdFile -Force -ErrorAction SilentlyContinue
                }
            }

            $appProc = Start-JeopardyApp -RepoRoot $repoRoot -Port $Port -Install:$Install
            $appProc.Id | Out-File -FilePath $appProcessIdFile -Encoding ascii
            Write-Output "Started app (PID $($appProc.Id)). PID file: $appProcessIdFile"

            Write-Info "Admin:  $HostUrl`:$Port/admin"
            Write-Info "Board:  $HostUrl`:$Port/board"
            Write-Info "Player: $HostUrl`:$Port/? (lobby)"

            if ($OpenBrowser) {
                Start-Process "$HostUrl`:$Port/admin" | Out-Null
                Start-Sleep -Milliseconds 250
                Start-Process "$HostUrl`:$Port/board" | Out-Null
            }
        }
    }

    'stop' {
        if (Test-Path $tunnelProcessIdFile) {
            $tunnelProcessId = Get-Content $tunnelProcessIdFile
            if (Get-Process -Id $tunnelProcessId -ErrorAction SilentlyContinue) {
                Write-Output "Stopping cloudflared (PID $tunnelProcessId)..."
                Stop-Process -Id $tunnelProcessId -Force
                Write-Output "Stopped cloudflared"
            } else {
                Write-Output "No running cloudflared process with PID $tunnelProcessId."
            }
            Remove-Item $tunnelProcessIdFile -Force -ErrorAction SilentlyContinue
        } else {
            Write-Output "No pid file for cloudflared found."
        }

        if (Test-Path $appProcessIdFile) {
            $appProcessId = Get-Content $appProcessIdFile
            if (Get-Process -Id $appProcessId -ErrorAction SilentlyContinue) {
                Write-Output "Stopping app (PID $appProcessId)..."
                Stop-Process -Id $appProcessId -Force
                Write-Output "Stopped app"
            } else {
                Write-Output "No running app process with PID $appProcessId."
            }
            Remove-Item $appProcessIdFile -Force -ErrorAction SilentlyContinue
        }
    }

    'status' {
        if (Test-Path $tunnelProcessIdFile) {
            $tunnelProcessId = Get-Content $tunnelProcessIdFile
            if (Get-Process -Id $tunnelProcessId -ErrorAction SilentlyContinue) {
                Write-Output "cloudflared running (PID $tunnelProcessId)."
            } else {
                Write-Output "cloudflared PID file exists but process not running."
            }
        } else {
            Write-Output "cloudflared not running (no pid file)."
        }

        if (Test-Path $appProcessIdFile) {
            $appProcessId = Get-Content $appProcessIdFile
            if (Get-Process -Id $appProcessId -ErrorAction SilentlyContinue) {
                Write-Output "app.py running (PID $appProcessId)."
            } else {
                Write-Output "app pid file exists but process not running."
            }
        } else {
            Write-Output "app not running (no pid file)."
        }
    }
}
