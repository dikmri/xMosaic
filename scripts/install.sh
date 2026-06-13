#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="${XMOSAIC_REPOSITORY:-dikmri/xMosaic}"
TAG="${XMOSAIC_INSTALL_TAG:-latest}"
SYSTEM="$(uname -s)"
MACHINE="$(uname -m)"

case "$SYSTEM" in
  Darwin) OS_NAME="macos" ;;
  Linux) OS_NAME="linux" ;;
  *) echo "Unsupported OS: $SYSTEM" >&2; exit 1 ;;
esac

case "$MACHINE" in
  x86_64|amd64) ARCH_NAME="x64" ;;
  arm64|aarch64) ARCH_NAME="arm64" ;;
  *) echo "Unsupported CPU architecture: $MACHINE" >&2; exit 1 ;;
esac

if [[ -n "${XMOSAIC_INSTALL_ROOT:-}" ]]; then
  INSTALL_ROOT="$XMOSAIC_INSTALL_ROOT"
elif [[ "$OS_NAME" == "macos" ]]; then
  INSTALL_ROOT="$HOME/Library/Application Support/xMosaic"
else
  INSTALL_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}/xMosaic"
fi

BIN_DIR="${XMOSAIC_BIN_DIR:-$HOME/.local/bin}"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/xmosaic-install.XXXXXX")"

cleanup() {
  rm -rf "$TMP_ROOT"
}
trap cleanup EXIT

step() {
  printf '==> %s\n' "$1"
}

have() {
  command -v "$1" >/dev/null 2>&1
}

as_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    "$@"
  elif have sudo; then
    sudo "$@"
  else
    echo "sudo is required to install missing system dependencies." >&2
    exit 1
  fi
}

install_macos_dependency() {
  local package="$1"
  if ! have brew; then
    echo "Homebrew is required to install missing dependency: $package" >&2
    echo "Install Homebrew or install $package manually, then run this script again." >&2
    exit 1
  fi
  brew install "$package"
}

install_linux_dependencies() {
  if have apt-get; then
    as_root apt-get update
    as_root apt-get install -y curl python3 python3-venv python3-pip ffmpeg tar gzip
  elif have dnf; then
    as_root dnf install -y curl python3 python3-pip ffmpeg tar gzip
  elif have yum; then
    as_root yum install -y curl python3 python3-pip ffmpeg tar gzip
  elif have pacman; then
    as_root pacman -Sy --needed --noconfirm curl python python-pip ffmpeg tar gzip
  elif have zypper; then
    as_root zypper install -y curl python3 python3-pip ffmpeg tar gzip
  elif have apk; then
    as_root apk add --no-cache curl python3 py3-pip ffmpeg tar gzip
  else
    echo "Install curl, Python 3, venv support, FFmpeg, tar, and gzip, then run this script again." >&2
    exit 1
  fi
}

ensure_dependencies() {
  if [[ "$OS_NAME" == "macos" ]]; then
    have curl || install_macos_dependency curl
    have python3 || install_macos_dependency python
    have ffmpeg || install_macos_dependency ffmpeg
    have ffprobe || install_macos_dependency ffmpeg
    return
  fi

  if ! have curl || ! have python3 || ! have ffmpeg || ! have ffprobe; then
    install_linux_dependencies
  fi
}

release_api_url() {
  if [[ "$TAG" == "latest" ]]; then
    printf 'https://api.github.com/repos/%s/releases/latest' "$REPOSITORY"
  else
    printf 'https://api.github.com/repos/%s/releases/tags/%s' "$REPOSITORY" "$TAG"
  fi
}

find_asset_url() {
  local pattern="$1"
  python3 - "$TMP_ROOT/release.json" "$pattern" <<'PY'
import fnmatch
import json
import sys

release_path, pattern = sys.argv[1], sys.argv[2]
release = json.load(open(release_path, encoding="utf-8"))
for asset in release.get("assets", []):
    if fnmatch.fnmatch(asset.get("name", ""), pattern):
        print(asset["browser_download_url"])
        raise SystemExit(0)
print(f"Release asset not found: {pattern}", file=sys.stderr)
raise SystemExit(1)
PY
}

download_asset() {
  local pattern="$1"
  local output="$2"
  local url
  url="$(find_asset_url "$pattern")"
  curl -fL --retry 3 -H "User-Agent: xMosaic-installer" "$url" -o "$output"
}

install_python_worker() {
  local wheel_path="$1"
  local venv_path="$INSTALL_ROOT/python"
  if [[ ! -x "$venv_path/bin/python" ]]; then
    step "Creating Python environment"
    python3 -m venv "$venv_path"
  fi

  step "Installing Python worker package"
  "$venv_path/bin/python" -m pip install --upgrade pip
  "$venv_path/bin/python" -m pip install --upgrade "$wheel_path"

  mkdir -p "$BIN_DIR"
  ln -sf "$venv_path/bin/xmosaic" "$BIN_DIR/xmosaic"
  printf '%s\n' "$venv_path/bin/python" > "$INSTALL_ROOT/python-path.txt"
}

install_macos_app() {
  local dmg_path="$1"
  local mount_dir="$TMP_ROOT/mount"
  local app_dest="${XMOSAIC_MAC_APP_DIR:-$HOME/Applications}"
  mkdir -p "$mount_dir" "$app_dest"

  step "Installing macOS app"
  hdiutil attach "$dmg_path" -mountpoint "$mount_dir" -nobrowse -quiet
  local app_path
  app_path="$(find "$mount_dir" -maxdepth 2 -name 'xMosaic.app' -type d | head -n 1)"
  if [[ -z "$app_path" ]]; then
    hdiutil detach "$mount_dir" -quiet || true
    echo "xMosaic.app was not found in the DMG." >&2
    exit 1
  fi
  rm -rf "$app_dest/xMosaic.app"
  cp -R "$app_path" "$app_dest/"
  hdiutil detach "$mount_dir" -quiet
}

install_linux_app() {
  local setup_archive="$1"
  local extract_dir="$TMP_ROOT/desktop"
  mkdir -p "$extract_dir"

  step "Installing Linux app"
  tar -xzf "$setup_archive" -C "$extract_dir"
  local setup_path
  setup_path="$(find "$extract_dir" -maxdepth 3 -type f -name 'xMosaic*Setup*' | head -n 1)"
  if [[ -z "$setup_path" ]]; then
    setup_path="$(find "$extract_dir" -maxdepth 3 -type f -name 'xMosaicSetup*' | head -n 1)"
  fi
  if [[ -z "$setup_path" ]]; then
    echo "xMosaic setup executable was not found in the Linux archive." >&2
    exit 1
  fi
  chmod +x "$setup_path"
  "$setup_path"
}

mkdir -p "$INSTALL_ROOT"
ensure_dependencies

step "Resolving xMosaic release"
curl -fsSL -H "User-Agent: xMosaic-installer" "$(release_api_url)" -o "$TMP_ROOT/release.json"

wheel_path="$TMP_ROOT/xmosaic.whl"
step "Downloading Python worker"
download_asset 'xmosaic-*-py3-none-any.whl' "$wheel_path"
install_python_worker "$wheel_path"

if [[ "$OS_NAME" == "macos" ]]; then
  dmg_path="$TMP_ROOT/xMosaic.dmg"
  step "Downloading macOS desktop app"
  download_asset "stable-macos-${ARCH_NAME}-xMosaic.dmg" "$dmg_path"
  install_macos_app "$dmg_path"
  step "Installation complete"
  echo "Launch xMosaic from $HOME/Applications."
else
  setup_path="$TMP_ROOT/xMosaicSetup.tar.gz"
  step "Downloading Linux desktop app"
  download_asset "stable-linux-${ARCH_NAME}-xMosaicSetup.tar.gz" "$setup_path"
  install_linux_app "$setup_path"
  step "Installation complete"
  echo "Launch xMosaic from your application menu."
fi

echo "CLI command: $BIN_DIR/xmosaic"
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "Add this to PATH if needed: export PATH=\"$BIN_DIR:\$PATH\""
fi
