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
mkdir -p "$APP/Contents/Resources"
cp "$ROOT/macos/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
cmp "$ROOT/macos/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
for color in white black blue; do
  cp "$ROOT/macos/AppIcon-$color.icns" "$APP/Contents/Resources/AppIcon-$color.icns"
  cmp "$ROOT/macos/AppIcon-$color.icns" "$APP/Contents/Resources/AppIcon-$color.icns"
done
/usr/libexec/PlistBuddy -c "Print :CFBundleIconFile" "$APP/Contents/Info.plist" | grep -Fxq AppIcon.icns
if [[ -n "${AJAZZ_HIGHSIERRA_BUILD_NUMBER:-}" ]]; then
  [[ "$AJAZZ_HIGHSIERRA_BUILD_NUMBER" =~ ^[1-9][0-9]*$ ]] || {
    echo "FAIL: expected a positive numeric High Sierra build number"
    exit 1
  }
  /usr/libexec/PlistBuddy -c     "Set :CFBundleVersion $AJAZZ_HIGHSIERRA_BUILD_NUMBER" "$APP/Contents/Info.plist"
fi
SDK="$(xcrun --sdk macosx --show-sdk-path)"
xcrun clang -O2 -fobjc-arc -Wall -Wextra   -target x86_64-apple-macosx10.13 -isysroot "$SDK"   -framework AppKit -framework Foundation -framework CoreBluetooth   -framework IOKit "$ROOT/macos/high-sierra/main.m" \
  "$ROOT/macos/high-sierra/diagnostic_runner.m" -o "$EXE"
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
  AJAZZ_TEST_CORPUS="$ROOT/tests/fixtures/apex-f7-v1.csv" "$EXE" --self-test
  "$EXE" --self-test-routine-poll
  "$EXE" --self-test-menu-diagnostic
  "$EXE" --help
else
  echo "SKIP: executable smoke test needs Intel runner"
fi
bash "$ROOT/macos/package-app.sh" "$APP" "$ZIP"
(cd "$ROOT/dist" && shasum -a 256 "$(basename "$ZIP")"   > AJAZZBatteryTray-macOS-HighSierra-Intel.sha256)
echo "PASS: $ZIP"
