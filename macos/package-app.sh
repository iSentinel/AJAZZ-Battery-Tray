#!/bin/bash
# Archive a built and signed app with stable entry order and timestamps.
set -euo pipefail

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: bash macos/package-app.sh APP_PATH OUTPUT_ZIP"
  exit 0
fi
if [[ $# != 2 || ! -d "$1" || -L "$1" ]]; then
  echo "FAIL: expected a built app directory and output ZIP" >&2
  exit 2
fi

APP_DIR="$(cd "$(dirname "$1")" && pwd)"
APP_NAME="$(basename "$1")"
OUTPUT_DIR="$(cd "$(dirname "$2")" && pwd)"
OUTPUT="$OUTPUT_DIR/$(basename "$2")"
STAGE="$(mktemp -d "$OUTPUT_DIR/.ajazz-zip.XXXXXXXX")"
trap 'rm -rf -- "$STAGE"' EXIT

(
  export LC_ALL=C TZ=UTC
  unset ZIPOPT
  cd "$APP_DIR"
  if [[ -n "$(find "./$APP_NAME" ! -type d ! -type f -print)" ]]; then
    echo "FAIL: app archive contains a link or special file" >&2
    exit 2
  fi
  # The fixed DOS-compatible time avoids local clock and time zone differences.
  # Package metadata changes do not alter the signed contents.
  find "./$APP_NAME" -exec touch -t 200001010000 {} +
  find "$APP_NAME" -print | sort | /usr/bin/zip -q -X "$STAGE/app.zip" -@
)
mv -f -- "$STAGE/app.zip" "$OUTPUT"
