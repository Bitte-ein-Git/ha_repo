# HA App: 🔊 Shairport-Sync • Airplay receiver

Turns your Home Assistant into an AirPlay 1 receiver and streams the audio (as 320kbps MP3) directly to your browser. Includes live metadata and album cover art.

## Features
* AirPlay 1 audio receiver (Shairport-Sync)
* Zero memory leaks thanks to direct pipe architecture (FFmpeg -> Node.js)
* Universally playable web stream (MP3 320kbps)
* Live JSON endpoint for metadata (Title, Artist, Album, ...)
* Live endpoint for current album cover

## Usage
Once you stream music from your iPhone/Mac to the configured speaker, use these endpoints (replace `<HA-IP>` with your HA IP):

* 1. **Audio Stream:** `http://<HA-IP>:8090/stream`
  - Returns the live audio stream.
  - **Content-Type:** `audio/mpeg`
  - **Quality:** 320kbps MP3, 44.1kHz, Stereo (from s16le raw data)

* 2. **Metadata (JSON):** `http://<HA-IP>:8090/meta`
  - Returns the current playback state as JSON. Automatically clears on disconnects.
  **Example:**
    ```json
    {
      "isPlaying": true,
      "title": "Never Gonna Give You Up",
      "artist": "Rick Astley",
      "album": "Whenever You Need Somebody"
    }

* 3. **Cover Art (JPEG):** `http://<HA-IP>:8090/cover`

## Configuration
Simple configuration via the Home Assistant UI.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `name` | String | `HA AirPlay` | The speaker name displayed in AirPlay menu. |
| `port` | Integer | `8090` | Port for the Node.js web server. Must be available in `host_network` mode. |