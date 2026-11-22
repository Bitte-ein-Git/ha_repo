#!/usr/bin/env bash
set -e

PORT=$(jq -r '.port // 3000' /data/options.json)
LOG_LEVEL=$(jq -r '.log_level // "info"' /data/options.json)

mkdir -p /data/pelagica_config

export CONFIG_PATH=/data/pelagica_config
export PORT=$PORT

if [ -n "$INGRESS_PATH" ]; then
    export BASE_PATH="$INGRESS_PATH"
fi

cd /app
exec ./pelagica-server