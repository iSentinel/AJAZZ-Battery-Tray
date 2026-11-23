#!/bin/bash
# macOS 10.13 hardware acceptance helper; no serial numbers or device configuration.
set -uo pipefail

usage() {
    cat <<'HELP'
Usage: bash macos/high-sierra/acceptance.sh [--dry-run] [--trace] [--app PATH] [-h|--help]

Read-only-in-purpose battery telemetry; F7 is sent as a HID Feature request.
The --trace option explicitly runs the same F7/05 query with bounded output.
No firmware, buttons, dock settings, or other device configuration is changed.

Exit codes: 0 PASS; 1 FAIL; 2 INCONCLUSIVE (device battery unknown).
To save a report locally, redirect stdout to a file and review before sharing.
HELP
}

APP="/Applications/AJAZZ Battery Tray High Sierra.app"
DRY=0
TRACE=0
while [ "$#" -gt 0 ]; do
    case "$1" in
        -h|--help) usage; exit 0 ;;
        --dry-run) DRY=1; shift ;;
        --trace) TRACE=1; shift ;;
        --app)
            if [ "$#" -lt 2 ] || [ -z "$2" ]; then
                echo "FAIL: --app requires an application path"
                exit 1
            fi
            APP="$2"
            shift 2
            ;;
        *)
            echo "FAIL: unknown option $1"
            usage
            exit 1
            ;;
    esac
done

EXE="$APP/Contents/MacOS/AJAZZBatteryTrayHighSierra"
if [ "$DRY" -eq 1 ]; then
    echo "DRY-RUN: no HID or Bluetooth requests will be issued"
    printf 'App: %s\n' "$APP"
    printf 'Would run: "%s" --self-test\n' "$EXE"
    printf 'Would run: "%s" --diagnose\n' "$EXE"
    if [ "$TRACE" -eq 1 ]; then
        printf 'Would run: "%s" --trace-hid\n' "$EXE"
    fi
    echo "Manual checks: menu bar, USB disconnect/reconnect, sleep/wake, notifications"
    exit 0
fi

if [ "$(uname -s)" != "Darwin" ]; then
    echo "FAIL: this acceptance test must run on macOS"
    exit 1
fi

OS="$(sw_vers -productVersion)"
ARCH="$(uname -m)"
MODEL="$(sysctl -n hw.model 2>/dev/null || echo unavailable)"
printf 'System: macOS %s / %s / %s\n' "$OS" "$ARCH" "$MODEL"
if [ "$ARCH" != "x86_64" ]; then
    echo "FAIL: this package is Intel x86_64 only"
    exit 1
fi
case "$OS" in
    10.13.*) echo "PASS: macOS High Sierra 10.13 target" ;;
    *)
        echo "INCONCLUSIVE: running outside macOS 10.13 (can test app only)"
        ;;
esac

if [ ! -x "$EXE" ]; then
    echo "FAIL: application executable missing or not executable"
    exit 1
fi

if "$EXE" --self-test; then
    echo "PASS: native offline regression checks"
else
    echo "FAIL: self-test exited unsuccessfully"
    exit 1
fi

OUTPUT="$("$EXE" --diagnose 2>&1)"
CODE="$?"
printf '%s\n' "$OUTPUT"
if [ "$CODE" -eq 0 ]; then
    echo "PASS: verified USB battery telemetry"
elif [ "$CODE" -eq 2 ] || [ "$CODE" -eq 124 ]; then
    echo "INCONCLUSIVE: receiver unreadable, or HID read timed out"
    CODE=2
else
    echo "FAIL: diagnostic executable failed unexpectedly"
    exit 1
fi

if [ "$TRACE" -eq 1 ]; then
    if ! "$EXE" --help | grep -Fq -- '--trace-hid'; then
        echo "FAIL: this edition has no --trace-hid; install High Sierra .4 or newer"
        exit 1
    fi
    TRACE_OUTPUT="$("$EXE" --trace-hid 2>&1)"
    TRACE_CODE="$?"
    printf '%s\n' "$TRACE_OUTPUT"
    if [ "$TRACE_CODE" -eq 0 ]; then
        CODE=0
        echo "PASS: verified F7/05 HID trace"
    elif [ "$TRACE_CODE" -eq 2 ] || [ "$TRACE_CODE" -eq 124 ]; then
        CODE=2
        echo "INCONCLUSIVE: trace unverified or timed out"
    else
        echo "FAIL: trace command failed unexpectedly"
        exit 1
    fi
    echo "Review response-prefix bytes before sharing this report."
fi

cat <<'MANUAL'
Manual High Sierra acceptance still required:
- Confirm menu bar icon and selection work.
- Check receiver unplug / reconnect: no false 0% or low battery.
- Let the mouse sleep, then wake it: no false receiver-disconnect event.
- Opt in to alerts and verify actual 50/25/10 behaviour.
- If applicable, manually select a connected AJAZZ BLE mouse to read 180F/2A19.
- Check settings EN/RU/UA; never paste serial numbers in issues.
MANUAL
if [ "$OS" != "10.13" ] && [[ "$OS" != 10.13.* ]]; then
    echo "INCONCLUSIVE: real High Sierra validation not possible on this macOS"
    exit 2
fi
if [ "$CODE" -eq 2 ]; then
    exit 2
fi
echo "PASS: automatic tests only; manual acceptance is still pending"
