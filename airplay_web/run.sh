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
# disable ffmpeg buffering and force immediate packet flushing for low latency
ffmpeg -loglevel error -fflags nobuffer -flags low_delay -f s16le -ar 44100 -ac 2 -i /tmp/audio_fifo \
    -c:a libmp3lame -b:a 320k -flush_packets 1 -f mp3 - | node /app/server.js $PORT