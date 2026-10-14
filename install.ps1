# One-command setup for story-dna on Windows 10/11: the app runs inside WSL2 (Ubuntu).
# Run from the story-dna folder in PowerShell:
#   powershell -ExecutionPolicy Bypass -File .\install.ps1
# Options: -Distro Ubuntu  -Target story-dna  (folder in the Linux home)  plus any install.sh flags, e.g.
#   .\install.ps1 --no-whisperx
param(
  [string]$Distro = "Ubuntu",
  [string]$Target = "story-dna",
  [Parameter(ValueFromRemainingArguments = $true)][string[]]$InstallArgs
)
$ErrorActionPreference = "Stop"

function Say($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "  [!] $msg" -ForegroundColor Yellow }

# wsl.exe prints UTF-16; strip the NULs so the text can be compared.
function Wsl-Text { (& wsl.exe @args 2>$null | Out-String) -replace "`0", "" }

Say "story-dna setup for Windows (WSL2 + $Distro)"

# 1. WSL2 and the Linux distribution
if (-not (Get-Command wsl.exe -ErrorAction SilentlyContinue)) {
  throw "wsl.exe not found. Windows 10 2004+ or Windows 11 is required."
}
$distros = (Wsl-Text -l -q) -split "`r?`n" | ForEach-Object { $_.Trim() } | Where-Object { $_ }
if ($distros -notcontains $Distro) {
  $admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator)
  if (-not $admin) {
    Warn "$Distro is not installed. Open PowerShell as Administrator and run this script again."
    exit 1
  }
  Say "Installing WSL2 + $Distro (Windows may ask to restart)"
  wsl.exe --install -d $Distro
  Write-Host ""
  Write-Host "When $Distro opens, create your Linux user name and password."
  Write-Host "If Windows asks for a restart: restart, then run this script again (not as Administrator)."
  exit 0
}

# 2. Copy the project into the Linux home (much faster than running it from C:\)
$here = $PSScriptRoot
$src = (Wsl-Text -d $Distro -- wslpath -a "$here").Trim()
Say "Copying the project to ~/$Target inside $Distro"
$copy = @"
set -e
if [ -d ~/$Target ]; then echo '  ~/$Target exists: code updated; data/, .venv and .env are kept'; fi
mkdir -p ~/$Target
cd '$src'
tar --exclude=./.venv --exclude=./data --exclude=./.env --exclude=./web/node_modules -cf - . | (cd ~/$Target && tar -xf -)
# A Windows checkout may have CRLF line ends: bash cannot run those
find ~/$Target -maxdepth 1 -name '*.sh' -exec sed -i 's/\r`$//' {} +
"@
wsl.exe -d $Distro -- bash -lc $copy

# 3. Run the Linux installer
Say "Running install.sh inside $Distro"
$argsLine = ($InstallArgs | ForEach-Object { "'$_'" }) -join " "
wsl.exe -d $Distro -- bash -lc "cd ~/$Target && chmod +x install.sh run_app.sh && ./install.sh $argsLine"

Write-Host ""
Say "Done. Every time you want to use story-dna:"
Write-Host "  wsl -d $Distro -- bash -lc 'cd ~/$Target && ./run_app.sh'"
Write-Host "  then open http://127.0.0.1:8765/ui/ in your Windows browser."
Write-Host "  First time only: log in to Claude inside ${Distro}:  wsl -d $Distro -- bash -lc claude"
