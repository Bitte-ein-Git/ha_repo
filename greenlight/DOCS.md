# Greenlight Add-on Documentation

## How it works

The add-on runs the headless WebUI version of Greenlight (Node.js + Express + static Next.js export), with a mobile-first Remote Play UI layered on top.

Persistent data (settings, tokens, store) is under `/data`.

On every start `/run.sh`:

1. Reads options from `/data/options.json`
2. Writes a fresh `manifest.webmanifest` (PWA name defaults to **RemotePlay**)
3. Starts `main/application.ts` with the configured port and optional access secret

## UI

- **Consoles** tab: list of consoles with power state and “Start Remote Play”
- **Settings** tab: account, streaming, input, video/audio, web UI, debug
- xCloud library is not linked from the main navigation
- Friends sidebar is hidden
- While streaming, top/bottom chrome is hidden for a clean player surface

## PWA

Manifest served at `/manifest.webmanifest` and `/manifest.json`.

Includes `apple-mobile-web-app-*` meta tags and logo as touch icon / startup image.

Change name, colors or display mode in add-on options and restart, then re-add to home screen if needed.

## Media Session

During an active stream the page sets `navigator.mediaSession` with:

- **title**: console id / name from the route
- **artist**: `Remote Play`
- **album**: `Xbox`
- artwork from `/images/logo.png`

So lock-screen / notification media UI can show the session.

## Access secret

Set `webui_access_secret`. Clients must open:

```
http://<host>:<port>/?secret=<your-secret>
```

WebSocket IPC uses the same secret.

## Troubleshooting

- **Blank page / login loop** – clear browser cache or private window; check add-on logs.
- **PWA not offered** – needs HTTPS (or localhost). Put a reverse proxy with TLS in front of the port if required.
- **Build failures on first install** – Dockerfile clones/builds upstream at image-build time; host needs internet.

## Upstream

https://github.com/pccr10001/greenlight-webonly  
Original: https://github.com/unknownskl/greenlight
