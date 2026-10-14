#!/usr/bin/env bash
# One-command setup for story-dna on Linux (Ubuntu/Debian, Fedora, Arch), WSL2 and macOS.
# Safe to run again: every step skips what is already installed.
#
#   ./install.sh                 full setup (asks before sudo installs)
#   ./install.sh --yes           no questions
#   ./install.sh --no-whisperx   skip WhisperX (~2.5 GB): dialogue is then guessed from frames
#   ./install.sh --no-codex      skip the Codex CLI (reference images)
#   ./install.sh --check         only report what is installed
set -euo pipefail
cd "$(dirname "$0")"

YES=0; WHISPERX=1; CODEX=1; CHECK_ONLY=0
for arg in "$@"; do
  case "$arg" in
    -y|--yes) YES=1 ;;
    --no-whisperx) WHISPERX=0 ;;
    --no-codex) CODEX=0 ;;
    --check) CHECK_ONLY=1 ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $arg (see --help)" >&2; exit 2 ;;
  esac
done

UV="$HOME/.local/bin/uv"
PY=".venv/bin/python"
export PATH="$HOME/.local/bin:$PATH"

if [ -t 1 ]; then B=$'\e[1m'; G=$'\e[32m'; Y=$'\e[33m'; R=$'\e[31m'; N=$'\e[0m'; else B=; G=; Y=; R=; N=; fi
step() { printf '\n%s==> %s%s\n' "$B" "$1" "$N"; }
ok()   { printf '  %s[ok]%s %s\n' "$G" "$N" "$1"; }
warn() { printf '  %s[!]%s %s\n' "$Y" "$N" "$1"; }
die()  { printf '  %s[x]%s %s\n' "$R" "$N" "$1" >&2; exit 1; }
have() { command -v "$1" >/dev/null 2>&1; }
ask()  { [ "$YES" = 1 ] && return 0; [ -t 0 ] || return 0; read -r -p "  $1 [Y/n] " a; [[ -z "$a" || "$a" =~ ^[Yy] ]]; }

# ---------- detect the system ----------
OS=$(uname -s); ARCH=$(uname -m); PM=""; DISTRO="$OS"; WSL=0
if [ "$OS" = "Darwin" ]; then
  DISTRO="macOS $(sw_vers -productVersion 2>/dev/null || true)"; PM=brew
elif [ "$OS" = "Linux" ]; then
  [ -r /etc/os-release ] && DISTRO=$(. /etc/os-release; echo "${PRETTY_NAME:-Linux}")
  grep -qi microsoft /proc/version 2>/dev/null && WSL=1
  if have apt-get; then PM=apt; elif have dnf; then PM=dnf; elif have pacman; then PM=pacman; elif have zypper; then PM=zypper; fi
else
  die "Unsupported system: $OS. On Windows run install.ps1 (it sets up WSL2 and runs this script inside)."
fi
SUDO=""; [ "$(id -u)" != 0 ] && have sudo && SUDO=sudo

pkg_install() {  # pkg_install <apt names> | <dnf names> | <pacman names> | <zypper names> | <brew names>
  local names
  case "$PM" in
    apt) names=$1 ;; dnf) names=$2 ;; pacman) names=$3 ;; zypper) names=$4 ;; brew) names=$5 ;;
    *) warn "No known package manager: install manually: $1"; return 1 ;;
  esac
  ask "Install $names with $PM?" || { warn "skipped: $names"; return 1; }
  case "$PM" in
    apt) $SUDO apt-get update -qq && $SUDO env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $names ;;
    dnf) $SUDO dnf install -y -q $names ;;
    pacman) $SUDO pacman -Sy --noconfirm --needed $names ;;
    zypper) $SUDO zypper -n -q install $names ;;
    brew) brew install $names ;;
  esac
}

check_report() {
  step "Check"
  local missing=0
  for b in ffmpeg ffprobe; do have "$b" && ok "$b" || { warn "$b missing (needed to read videos)"; missing=1; }; done
  [ -x "$PY" ] && ok "Python env .venv ($($PY --version 2>&1))" || { warn ".venv missing"; missing=1; }
  if [ -x "$PY" ] && $PY -c "import fastapi, uvicorn" 2>/dev/null; then ok "web app packages"; else warn "web app packages missing"; missing=1; fi
  if [ -x "$PY" ] && $PY -c "import whisperx" 2>/dev/null; then ok "WhisperX (real dialogue transcripts)"
  else warn "WhisperX not installed: dialogue is guessed from frames (rerun without --no-whisperx)"; fi
  if [ -x "$PY" ]; then
    local env; env=$($PY -c "from app import config; e = config.check_environment(); print(e['claude_bin'] or '', '|', e['codex_bin'] or '', sep='')" 2>/dev/null || echo "|")
    [ -n "${env%%|*}" ] && ok "Claude Code: ${env%%|*}" || { warn "Claude Code CLI not found (required)"; missing=1; }
    [ -n "${env#*|}" ] && ok "Codex: ${env#*|}" || warn "Codex CLI not found (optional, reference images)"
  fi
  [ -f .env ] && grep -q '^HF_TOKEN=.\+' .env && ok "HF_TOKEN set (speaker labels)" || warn "HF_TOKEN not set (optional, speaker labels): edit .env"
  [ -f app/static/ui/index.html ] && ok "web UI build present" || warn "app/static/ui missing: cd web && npm install && npm run build"
  return $missing
}

printf '%sstory-dna setup%s  (%s, %s%s)\n' "$B" "$N" "$DISTRO" "$ARCH" "$([ $WSL = 1 ] && echo ', WSL2')"
if [ "$CHECK_ONLY" = 1 ]; then check_report && exit 0 || exit 1; fi

# ---------- 1. system packages ----------
step "1/6 System packages (ffmpeg, git, curl)"
if [ "$PM" = brew ] && ! have brew; then
  die "Homebrew is needed on macOS: install it from https://brew.sh, then run ./install.sh again."
fi
need=()
have curl || need+=(curl)
have git || need+=(git)
have ffmpeg && have ffprobe || need+=(ffmpeg)
if [ ${#need[@]} = 0 ]; then ok "ffmpeg, git, curl"
else
  # Fedora: the 'ffmpeg-free' build in the default repos works for common H.264/AAC files via openh264;
  # RPM Fusion's 'ffmpeg' is the full build.
  if [ "$PM" = dnf ]; then names=$(printf '%s ' "${need[@]}" | sed 's/ffmpeg/ffmpeg-free/')
  else names="${need[*]}"; fi
  pkg_install "$names" "$names" "$names" "$names" "$names" || true
  have ffmpeg && ok "ffmpeg $(ffmpeg -version | head -1 | awk '{print $3}')" || warn "ffmpeg still missing: install it, videos cannot be read without it"
fi

# ---------- 2. uv + Python ----------
step "2/6 uv and Python 3.12 environment (.venv)"
if [ ! -x "$UV" ] && ! have uv; then
  have curl || die "curl is needed to download uv: install curl, then run ./install.sh again."
  curl -LsSf https://astral.sh/uv/install.sh | env UV_NO_MODIFY_PATH=1 sh -s -- --quiet
fi
have uv && UV=$(command -v uv)
[ -x "$UV" ] || die "uv was not installed; see https://docs.astral.sh/uv/"
ok "uv $("$UV" --version | awk '{print $2}')"
if [ ! -x "$PY" ]; then "$UV" venv .venv --python 3.12 --quiet; fi
ok ".venv ($($PY --version 2>&1))"

# ---------- 3. web app packages ----------
step "3/6 Web app packages"
"$UV" pip install --quiet --python "$PY" -r app/requirements.txt
ok "fastapi, uvicorn, ..."

# ---------- 4. WhisperX ----------
step "4/6 WhisperX (local transcription, ~2.5 GB)"
if [ "$WHISPERX" = 0 ]; then warn "skipped (--no-whisperx)"
elif $PY -c "import whisperx" 2>/dev/null; then ok "already installed"
elif [ "$OS" = Darwin ] && [ "$ARCH" = x86_64 ]; then
  warn "Intel Mac: current PyTorch has no wheels for it; skipped. Dialogue will be guessed from frames."
else
  echo "  Downloading PyTorch (CPU) + WhisperX; this takes a few minutes..."
  if [ "$OS" = Darwin ]; then "$UV" pip install --quiet --python "$PY" whisperx
  else "$UV" pip install --quiet --python "$PY" whisperx \
         --extra-index-url https://download.pytorch.org/whl/cpu --index-strategy unsafe-best-match; fi
  $PY -c "import whisperx" 2>/dev/null && ok "WhisperX installed" || warn "WhisperX import failed; see the output above"
fi

# ---------- 5. Claude Code (required) + Codex (optional) ----------
step "5/6 Claude Code CLI (required) and Codex CLI (optional)"
claude_bin=$($PY -c "from app import config; print(config.find_claude_bin() or '')")
if [ -z "$claude_bin" ]; then
  if ask "Install Claude Code (official installer from claude.ai)?"; then
    curl -fsSL https://claude.ai/install.sh | bash || warn "Claude Code installer failed"
    claude_bin=$($PY -c "from app import config; print(config.find_claude_bin() or '')")
  fi
fi
[ -n "$claude_bin" ] && ok "Claude Code: $claude_bin" || warn "Claude Code missing: see https://docs.claude.com/claude-code"

codex_bin=$($PY -c "from app import config; print(config.find_codex_bin() or '')")
if [ "$CODEX" = 0 ]; then warn "Codex skipped (--no-codex)"
elif [ -n "$codex_bin" ]; then ok "Codex: $codex_bin"
elif [ "$PM" = brew ] && ask "Install the Codex CLI with Homebrew (reference images, uses your ChatGPT plan)?"; then
  brew install codex && ok "Codex installed" || warn "Codex install failed (optional)"
elif have npm && ask "Install the Codex CLI with npm (reference images, uses your ChatGPT plan)?"; then
  npm install -g @openai/codex --silent && ok "Codex installed" || warn "Codex install failed (optional)"
else
  warn "Codex not installed (optional): install Node.js, then npm install -g @openai/codex"
fi

# ---------- 6. settings ----------
step "6/6 Settings"
if [ ! -f .env ]; then cp .env.example .env; chmod 600 .env; ok ".env created (edit HF_TOKEN for speaker labels)"
else ok ".env kept"; fi
chmod +x run_app.sh
mkdir -p data/input

check_report || true

cat <<EOF

${B}Next${N}
  1. Log in to Claude once (opens a browser link):   claude
EOF
[ "$CODEX" = 1 ] && echo "  2. Optional, reference images, log in to Codex:  codex login"
cat <<EOF
  3. Start the app:                                  ./run_app.sh
     then open http://127.0.0.1:8765/ui/
EOF
[ $WSL = 1 ] && echo "  WSL2: open that address in your Windows browser; put videos under $(pwd)/data/input."
exit 0
