#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
export SDUI_DATA="${SDUI_DATA:-$DIR/.data}"
export SDUI_SHARE="${SDUI_SHARE:-$DIR/.share}"
export SDUI_CONFIG="${SDUI_CONFIG:-$DIR/options.local.json}"
mkdir -p "$SDUI_DATA" "$SDUI_SHARE"
if [[ ! -f "$SDUI_CONFIG" ]]; then
  cp "$DIR/options.example.json" "$SDUI_CONFIG"
  echo "Created $SDUI_CONFIG – edit credentials, then re-run."
  exit 1
fi
python3 "$DIR/rootfs/usr/bin/sdui-sync.py" --once
