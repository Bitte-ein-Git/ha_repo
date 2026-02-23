#!/usr/bin/env sh
set -e

NAME=$(jq -r '.name' /data/options.json)
PORT=$(jq -r '.port' /data/options.json)

sed -i "s/{{NAME}}/$NAME/g" /etc/shairport-sync.conf

# setup pipes for audio and metadata
rm -f /tmp/audio_fifo /tmp/shairport_metadata
mkfifo /tmp/audio_fifo
mkfifo /tmp/shairport_metadata

echo "Starting DBus..."
mkdir -p /var/run/dbus
dbus-daemon --system --fork

echo "Starting Avahi..."
avahi-daemon --daemonize

echo "Starting shairport-sync..."
shairport-sync -c /etc/shairport-sync.conf &

echo "Starting FFmpeg and Node server..."
# encode to 320kbps mp3 for max quality and universal browser compatibility
ffmpeg -loglevel error -f s16le -ar 44100 -ac 2 -i /tmp/audio_fifo \
    -c:a libmp3lame -b:a 320k -f mp3 - | node /app/server.js $PORT