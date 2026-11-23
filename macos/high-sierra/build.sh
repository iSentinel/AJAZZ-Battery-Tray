#!/bin/bash
# Objective-C Intel macOS 10.13 app; no Swift runtime dependencies.
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: bash macos/high-sierra/build.sh [--help]"
  exit 0
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$ROOT/dist/high-sierra/AJAZZ Battery Tray High Sierra.app"
EXE="$APP/Contents/MacOS/AJAZZBatteryTrayHighSierra"
ZIP="$ROOT/dist/AJAZZBatteryTray-macOS-HighSierra-Intel.zip"
mkdir -p "$APP/Contents/MacOS"
cp "$ROOT/macos/high-sierra/Info.plist" "$APP/Contents/Info.plist"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
xcrun clang -O2 -fobjc-arc -Wall -Wextra   -target x86_64-apple-macosx10.13 -isysroot "$SDK"   -framework AppKit -framework Foundation -framework CoreBluetooth   -framework IOKit "$ROOT/macos/high-sierra/main.m" -o "$EXE"
chmod 755 "$EXE"
plutil -lint "$APP/Contents/Info.plist"
file "$EXE" | grep -q 'x86_64'
if otool -L "$EXE" | grep -qi 'libswift'; then
  echo "FAIL: unexpected Swift runtime dependency"
  exit 1
fi
codesign --force --sign - "$APP"
codesign --verify --verbose "$APP"
if [[ "$(uname -m)" == "x86_64" ]]; then
  "$EXE" --self-test
  "$EXE" --help
else
  echo "SKIP: executable smoke test needs Intel runner"
fi
ditto -c -k --sequesterRsrc --keepParent "$APP" "$ZIP"
(cd "$ROOT/dist" && shasum -a 256 "$(basename "$ZIP")"   > AJAZZBatteryTray-macOS-HighSierra-Intel.sha256)
echo "PASS: $ZIP"
