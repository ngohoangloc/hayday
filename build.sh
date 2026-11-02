#!/usr/bin/env bash
# Build binary + AppImage trên Linux.
# Yêu cầu: python3 -m venv .venv đã cài requirements.txt + pyinstaller
set -e
cd "$(dirname "$0")"

PY="${PYTHON:-.venv/bin/python}"
"$PY" -m PyInstaller --noconfirm --clean hayday-bot.spec

rm -rf packaging/AppDir packaging/out
mkdir -p packaging/AppDir/usr/bin packaging/out
cp dist/hayday-bot packaging/AppDir/usr/bin/
cp packaging/hayday-bot.desktop packaging/AppDir/
cp packaging/hayday-bot.png packaging/AppDir/

if [ ! -f packaging/linuxdeploy-x86_64.AppImage ]; then
  curl -sL -o packaging/linuxdeploy-x86_64.AppImage \
    "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
  chmod +x packaging/linuxdeploy-x86_64.AppImage
fi

VERSION="${VERSION:-1.1.0}"
cd packaging
OUTPUT="hayday-bot-${VERSION}-x86_64.AppImage" \
  ./linuxdeploy-x86_64.AppImage --appimage-extract-and-run \
  --appdir AppDir \
  -d AppDir/hayday-bot.desktop \
  -i AppDir/hayday-bot.png \
  --output appimage

echo "Xong: packaging/hayday-bot-${VERSION}-x86_64.AppImage"
