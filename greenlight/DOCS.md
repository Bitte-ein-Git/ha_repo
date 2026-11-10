# Greenlight Add-on Documentation

## How it works

The add-on runs the headless WebUI version of Greenlight (Node.js + Express + static Next.js export).  
All persistent data (settings, tokens, store) is written under `/data` which Home Assistant maps for you.

On every start `/run.sh`:

1. Reads the options from `/data/options.json`
2. Writes a fresh `manifest.webmanifest` with your PWA settings
3. Starts `main/application.ts` with the configured port and optional access secret

## PWA / Home Screen App

The manifest is served at:

- `/manifest.webmanifest`
- `/manifest.json`

The frontend also contains the usual meta tags (`theme-color`, `apple-mobile-web-app-capable`, …).

Change the name, colors or display mode in the add-on configuration and restart – the next time you “Add to Home Screen” the new values are used.

## Access secret

Set `webui_access_secret` to any string.  
Clients must then open:

```
http://<host>:<port>/?secret=<your-secret>
```

WebSocket IPC is also protected by the same secret.

## Ports

| Container | Host (default) | Purpose |
|-----------|----------------|---------|
| 9003/tcp  | 9003           | WebUI   |

You can change the host mapping in the add-on “Network” section.

## Troubleshooting

- **Blank page / login loop** – clear browser cache or open in a private window. Check the add-on log for auth errors.
- **PWA not offered** – the page must be served over HTTPS (or localhost). When using the direct port this is only true if you put a reverse proxy with TLS in front.
- **Build failures on first install** – the Dockerfile clones and builds upstream at image-build time. Needs internet access on the machine that builds the add-on (HA OS does this automatically).

## Upstream

https://github.com/pccr10001/greenlight-webonly  
Original project: https://github.com/unknownskl/greenlight
