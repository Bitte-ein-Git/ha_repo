#!/bin/bash
set -e

# Define paths
USER_DATA_PATH="/config/mcxboxbroadcast"
APP_DIR="/opt/app/config"
CONFIG_FILE="$USER_DATA_PATH/config.yml"

# Create user data directory if it doesn't exist
if [ ! -d "$USER_DATA_PATH" ]; then
    echo "Creating config directory at $USER_DATA_PATH..."
    mkdir -p "$USER_DATA_PATH"
fi

# Parse Auth Reset Option
RESET_AUTH=$(jq --raw-output '.reset_auth // false' /data/options.json)

# --- Logout Logic ---
if [ "$RESET_AUTH" == "true" ]; then
    echo "!!! RESET AUTH OPTION ENABLED !!!"
    echo "Wiping cache to force re-authentication..."
    rm -rf "$USER_DATA_PATH/cache"
    rm -rf "$APP_DIR/cache" # Safety cleanup internal dir
    echo "Cache deleted. Please disable 'reset_auth' in addon configuration and restart to log in again."
    # We exit here to prevent the app from starting and creating a partial/broken cache immediately
    exit 0
fi
# --------------------

# --- Cache & File Linking ---
# Ensure cache directory exists
if [ ! -d "$USER_DATA_PATH/cache" ]; then
    mkdir -p "$USER_DATA_PATH/cache"
fi

# Fix permissions for the folder so the app user can read/write
chmod -R 777 "$USER_DATA_PATH"

# Clean internal config dir to prevent conflicts
rm -rf "$APP_DIR/cache"
rm -f "$APP_DIR/config.yml"
rm -f "$APP_DIR/screenshot.jpg"

# Link persistent cache
ln -s "$USER_DATA_PATH/cache" "$APP_DIR/cache"

# Link screenshot if exists
if [ -f "$USER_DATA_PATH/screenshot.jpg" ]; then
    echo "Custom screenshot found, linking..."
    ln -s "$USER_DATA_PATH/screenshot.jpg" "$APP_DIR/screenshot.jpg"
fi
# ----------------------------

# Parse options
REMOTE_ADDRESS=$(jq --raw-output '.remote_address // "auto"' /data/options.json)
REMOTE_PORT=$(jq --raw-output '.remote_port // "auto"' /data/options.json)
HOST_NAME=$(jq --raw-output '.host_name // "Geyser Server"' /data/options.json)
WORLD_NAME=$(jq --raw-output '.world_name // "GeyserMC Broadcast"' /data/options.json)
MAX_PLAYERS=$(jq --raw-output '.max_players // 20' /data/options.json)
UPDATE_INTERVAL=$(jq --raw-output '.update_interval // 30' /data/options.json)
DEBUG_LOG=$(jq --raw-output '.debug_log // false' /data/options.json)
FS_UPDATE_INTERVAL=$(jq --raw-output '.update_interval // 60' /data/options.json)
FS_AUTO_FOLLOW=$(jq --raw-output '.friend_sync.auto_follow // true' /data/options.json)
FS_AUTO_UNFOLLOW=$(jq --raw-output '.friend_sync.auto_unfollow // true' /data/options.json)
FS_INITIAL_INVITE=$(jq --raw-output '.friend_sync.initial_invite // true' /data/options.json)

# --- Fix "auto" IP for Standalone ---
if [ "$REMOTE_ADDRESS" == "auto" ]; then
    echo "IP set to 'auto'. Defaulting to 127.0.0.1 (Host Network Mode)"
    REMOTE_ADDRESS="127.0.0.1"
fi

# Generate config.yml in user path (so you can inspect it)
echo "Generating config.yml at $CONFIG_FILE..."
cat <<EOF > "$CONFIG_FILE"
session:
  update-interval: $UPDATE_INTERVAL
  query-server: true
  web-query-fallback: false
  config-fallback: true
  session-info:
    host-name: "$HOST_NAME"
    world-name: "$WORLD_NAME"
    players: 0
    max-players: $MAX_PLAYERS
    ip: "$REMOTE_ADDRESS"
    port: $REMOTE_PORT

friend-sync:
  update-interval: $FS_UPDATE_INTERVAL
  auto-follow: $FS_AUTO_FOLLOW
  auto-unfollow: $FS_AUTO_UNFOLLOW
  initial-invite: $FS_INITIAL_INVITE
  should-expire: true
  expire-days: 15
  expire-check: 1800

slack-webhook:
  enabled: false
  webhook-url: ""
  session-expired-message: |
    <!here> Xbox Session expired.
  friend-restriction-message: |
    Restrictions active.

debug-log: $DEBUG_LOG
suppress-session-update-info: false
EOF

# Link the generated config to the app location
ln -s "$CONFIG_FILE" "$APP_DIR/config.yml"

# Start application
echo "Starting MCXboxBroadcast..."
exec java -jar /opt/app/MCXboxBroadcastStandalone.jar