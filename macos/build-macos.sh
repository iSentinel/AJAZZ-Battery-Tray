#!/bin/bash
# Build unsigned (ad-hoc signed) universal macOS app on a macOS runner.
set -euo pipefail
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  echo "Usage: bash macos/build-macos.sh [--help]"
  exit 0
fi
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/dist/mac/AJAZZ Battery Tray.app"
OUT="$ROOT/dist/AJAZZBatteryTray-macOS-universal.zip"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp "$ROOT/macos/Info.plist" "$APP/Contents/Info.plist"
mkdir -p "$APP/Contents/Resources"
cp "$ROOT/macos/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
cmp "$ROOT/macos/AppIcon.icns" "$APP/Contents/Resources/AppIcon.icns"
for color in white black blue; do
  cp "$ROOT/macos/AppIcon-$color.icns" "$APP/Contents/Resources/AppIcon-$color.icns"
  cmp "$ROOT/macos/AppIcon-$color.icns" "$APP/Contents/Resources/AppIcon-$color.icns"
done
/usr/libexec/PlistBuddy -c "Print :CFBundleIconFile" "$APP/Contents/Info.plist" | grep -Fxq AppIcon.icns
SDK="$(xcrun --sdk macosx --show-sdk-path)"
for arch in arm64 x86_64; do
  swiftc -O -import-objc-header "$ROOT/macos/AjazzBatteryReport.h" -sdk "$SDK" -target "${arch}-apple-macos13.0" \
    -framework AppKit -framework IOKit -framework UserNotifications -framework ServiceManagement -framework CoreBluetooth \
    "$ROOT/macos/main.swift" "$ROOT/macos/AppText.swift" "$ROOT/macos/TrayAppearance.swift" "$ROOT/macos/ApexBoundedWorker.swift" \
    "$ROOT/macos/BatteryHistory.swift" \
    "$ROOT/macos/BatteryHistoryWindow.swift" \
    "$ROOT/macos/BatteryNotifications.swift" \
    "$ROOT/macos/BluetoothBattery.swift" -o "$ROOT/dist/mac/ajazz-${arch}"
done
lipo -create "$ROOT/dist/mac/ajazz-arm64" "$ROOT/dist/mac/ajazz-x86_64" \
  -output "$APP/Contents/MacOS/AJAZZBatteryTray"
chmod +x "$APP/Contents/MacOS/AJAZZBatteryTray"
codesign --force --deep --sign - "$APP"
plutil -lint "$APP/Contents/Info.plist"
codesign --verify --verbose "$APP"
"$APP/Contents/MacOS/AJAZZBatteryTray" --help
AJAZZ_TEST_CORPUS="$ROOT/tests/fixtures/apex-f7-v1.csv" "$APP/Contents/MacOS/AJAZZBatteryTray" --self-test
"$APP/Contents/MacOS/AJAZZBatteryTray" --self-test-bounded-poll
ditto -c -k --sequesterRsrc --keepParent "$APP" "$OUT"
shasum -a 256 "$OUT" | sed "s|$ROOT/dist/||" > "$ROOT/dist/AJAZZBatteryTray-macOS-universal.sha256"
echo "PASS: $OUT"
