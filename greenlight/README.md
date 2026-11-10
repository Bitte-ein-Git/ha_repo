# Greenlight – Home Assistant Add-on

Open-source **Xbox xCloud & Home streaming** client (Web-only fork) packaged as a Home Assistant add-on.

Based on [pccr10001/greenlight-webonly](https://github.com/pccr10001/greenlight-webonly).

## Features

- Full Greenlight WebUI (xCloud + console streaming)
- Gamepad / keyboard support in Chromium-based browsers
- Optional access secret
- **Customizable PWA manifest** – add the Xbox Remote Play page as a home-screen app on your phone
- Persistent settings & tokens under `/data`

## Installation

### As local add-on

1. Copy the whole `greenlight` folder into `/addons/greenlight` on your Home Assistant host (via Samba / SSH / Studio Code Server).
2. Go to **Settings → Add-ons → Add-on Store → ⋮ → Check for updates / Reload**.
3. The add-on “Greenlight” appears under **Local add-ons**. Install it.

### As repository (optional)

Create a Git repo that contains this folder + a `repository.yaml`:

```yaml
name: Greenlight Add-ons
url: https://github.com/YOUR_USER/ha-greenlight
maintainer: You
```

Then add the repo URL in the Add-on Store.

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `webui_port` | `9003` | Port the WebUI listens on (also mapped to the host) |
| `webui_access_secret` | empty | If set, append `?secret=YOURSECRET` to the URL |
| `pwa_name` | Xbox Remote Play | Full name shown when installing the PWA |
| `pwa_short_name` | Xbox Play | Short name under the home-screen icon |
| `pwa_theme_color` | `#107C10` | Theme / status-bar color (Xbox green) |
| `pwa_background_color` | `#000000` | Splash background |
| `pwa_display` | `standalone` | `fullscreen` / `standalone` / `minimal-ui` / `browser` |

After changing options, **restart** the add-on. The PWA manifest is regenerated on every start.

## Usage

1. Start the add-on.
2. Open the Web UI (button on the add-on page or `http://homeassistant.local:9003`).
3. Log in with your Microsoft / Xbox account (device-code flow works well).
4. On your phone: open the same URL in Chrome / Safari → “Add to Home Screen”. The custom name & icon from the PWA options will be used.

If you set an access secret, use:

```
http://homeassistant.local:9003/?secret=YOURSECRET
```

## Notes

- First start builds nothing at runtime – the image already contains a production build of Greenlight.
- Tokens and settings live in the add-on data directory and survive restarts.
- Streaming needs a reasonably fast network and a Chromium browser with WebRTC support.
- Not affiliated with Microsoft / Xbox.

## License

Same as upstream Greenlight (see LICENSE in the original repository).
