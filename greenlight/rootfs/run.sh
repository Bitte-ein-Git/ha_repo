#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH=/data/options.json

WEBUI_PORT=$(jq -r '.webui_port // 9003' "$CONFIG_PATH" 2>/dev/null || echo 9003)
ACCESS_SECRET=$(jq -r '.webui_access_secret // empty' "$CONFIG_PATH" 2>/dev/null || true)
PWA_NAME=$(jq -r '.pwa_name // "Xbox Remote Play"' "$CONFIG_PATH" 2>/dev/null || echo "Xbox Remote Play")
PWA_SHORT=$(jq -r '.pwa_short_name // "Xbox Play"' "$CONFIG_PATH" 2>/dev/null || echo "Xbox Play")
PWA_THEME=$(jq -r '.pwa_theme_color // "#107C10"' "$CONFIG_PATH" 2>/dev/null || echo "#107C10")
PWA_BG=$(jq -r '.pwa_background_color // "#000000"' "$CONFIG_PATH" 2>/dev/null || echo "#000000")
PWA_DISPLAY=$(jq -r '.pwa_display // "standalone"' "$CONFIG_PATH" 2>/dev/null || echo "standalone")

export NODE_ENV=production
export WEBUI_PORT
export WEBUI_ACCESS_SECRET="${ACCESS_SECRET:-}"

mkdir -p /data
cd /app
ln -sfn /data /app/data

# Customizable PWA manifest written on every start from addon options
cat > /data/manifest.webmanifest <<EOF
{
  "name": "${PWA_NAME}",
  "short_name": "${PWA_SHORT}",
  "description": "Xbox xCloud and Home streaming via Greenlight",
  "start_url": "/home",
  "scope": "/",
  "display": "${PWA_DISPLAY}",
  "orientation": "any",
  "theme_color": "${PWA_THEME}",
  "background_color": "${PWA_BG}",
  "icons": [
    {
      "src": "/images/logo.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "any maskable"
    },
    {
      "src": "/images/logo.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any maskable"
    }
  ]
}
EOF

# Keep a copy next to static export
mkdir -p /app/app
cp -f /data/manifest.webmanifest /app/app/manifest.webmanifest

echo "[greenlight] WebUI port=${WEBUI_PORT}"
echo "[greenlight] PWA: ${PWA_NAME} (${PWA_DISPLAY})"

exec npx tsx ./main/application.ts
