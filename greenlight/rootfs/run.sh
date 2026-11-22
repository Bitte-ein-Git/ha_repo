#!/usr/bin/env bash
set -euo pipefail

CONFIG_PATH=/data/options.json

WEBUI_PORT=$(jq -r '.webui_port // 9003' "$CONFIG_PATH" 2>/dev/null || echo 9003)
ACCESS_SECRET=$(jq -r '.webui_access_secret // empty' "$CONFIG_PATH" 2>/dev/null || true)
PWA_NAME=$(jq -r '.pwa_name // "RemotePlay"' "$CONFIG_PATH" 2>/dev/null || echo "RemotePlay")
PWA_SHORT=$(jq -r '.pwa_short_name // "RemotePlay"' "$CONFIG_PATH" 2>/dev/null || echo "RemotePlay")
PWA_THEME=$(jq -r '.pwa_theme_color // "#107C10"' "$CONFIG_PATH" 2>/dev/null || echo "#107C10")
PWA_BG=$(jq -r '.pwa_background_color // "#000000"' "$CONFIG_PATH" 2>/dev/null || echo "#000000")
PWA_DISPLAY=$(jq -r '.pwa_display // "standalone"' "$CONFIG_PATH" 2>/dev/null || echo "standalone")
UNMODIFIED=$(jq -r '.unmodified_webui // true' "$CONFIG_PATH" 2>/dev/null || echo true)

export NODE_ENV=production
export WEBUI_PORT
export WEBUI_ACCESS_SECRET="${ACCESS_SECRET:-}"

mkdir -p /data
cd /app
ln -sfn /data /app/data

# Pick static WebUI: stock (upstream) or mobile (RemotePlay patches)
rm -rf /app/app
if [ "$UNMODIFIED" = "true" ] || [ "$UNMODIFIED" = "True" ] || [ "$UNMODIFIED" = "1" ]; then
  echo "[greenlight] Unmodified WebUI (stock upstream)"
  cp -a /app/app-stock /app/app
else
  echo "[greenlight] Mobile / RemotePlay WebUI"
  cp -a /app/app-mobile /app/app

  cat > /data/manifest.webmanifest <<MANIFEST
{
  "name": "${PWA_NAME}",
  "short_name": "${PWA_SHORT}",
  "description": "Xbox Remote Play",
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
      "purpose": "any"
    },
    {
      "src": "/images/logo.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "any"
    },
    {
      "src": "/images/logo.png",
      "sizes": "192x192",
      "type": "image/png",
      "purpose": "maskable"
    },
    {
      "src": "/images/logo.png",
      "sizes": "512x512",
      "type": "image/png",
      "purpose": "maskable"
    }
  ]
}
MANIFEST
  cp -f /data/manifest.webmanifest /app/app/manifest.webmanifest
  echo "[greenlight] PWA: ${PWA_NAME} (${PWA_DISPLAY})"
fi

echo "[greenlight] WebUI port=${WEBUI_PORT}"

exec npx tsx ./main/application.ts
