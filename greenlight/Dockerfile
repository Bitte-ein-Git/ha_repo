ARG BUILD_FROM
FROM node:18-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git python3 make g++

ARG GREENLIGHT_REF=main-v2
RUN git clone --depth 1 -b ${GREENLIGHT_REF} https://github.com/pccr10001/greenlight-webonly.git .

# --- Mobile UI + PWA assets (copied before patches) ---
COPY rootfs/mobile.css renderer/mobile.css
COPY rootfs/header.mobile.tsx renderer/components/header.tsx
COPY rootfs/default-manifest.webmanifest renderer/public/manifest.webmanifest

# Import mobile.css at the end of styles.css
RUN echo '' >> renderer/styles.css \
 && echo '/* Mobile / responsive (HA addon) */' >> renderer/styles.css \
 && echo "@import 'mobile.css';" >> renderer/styles.css

# --- Patch webui.ts for HA port/secret + PWA manifest route ---
RUN node <<'EOF'
const fs = require('fs');
const p = 'main/webui.ts';
let s = fs.readFileSync(p, 'utf8');

s = s.replace(
  /this\.startServer\(settings\.webui_port\)/,
  `const port = Number(process.env.WEBUI_PORT) || settings.webui_port || 9003
        if (process.env.WEBUI_ACCESS_SECRET !== undefined && process.env.WEBUI_ACCESS_SECRET !== '') {
            settings.webui_access_secret = process.env.WEBUI_ACCESS_SECRET
            this._application._store.set('settings', settings)
        }
        this.startServer(port)`
);

const inject = `
        // Customizable PWA manifest (written by /run.sh from addon options)
        this._express.get(['/manifest.webmanifest', '/manifest.json'], (req, res) => {
            const fs = require('fs')
            const path = require('path')
            const candidates = [
                '/data/manifest.webmanifest',
                path.join(__dirname, '../app/manifest.webmanifest'),
            ]
            for (const cand of candidates) {
                if (fs.existsSync(cand)) {
                    res.type('application/manifest+json')
                    return res.sendFile(cand)
                }
            }
            res.status(404).json({ error: 'manifest not found' })
        })
`;
s = s.replace(
  'this._ipc = this._application._ipc',
  'this._ipc = this._application._ipc\n' + inject
);

fs.writeFileSync(p, s);
console.log('webui.ts patched');
EOF

# Inject PWA meta + viewport into _app.tsx Head
RUN node <<'EOF'
const fs = require('fs');
const p = 'renderer/pages/_app.tsx';
let s = fs.readFileSync(p, 'utf8');
if (!s.includes('manifest.webmanifest')) {
  const headBlock = `
                <Head>
                    <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
                    <link rel="manifest" href="/manifest.webmanifest" />
                    <meta name="theme-color" content="#107C10" />
                    <meta name="mobile-web-app-capable" content="yes" />
                    <meta name="apple-mobile-web-app-capable" content="yes" />
                    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
                    <link rel="apple-touch-icon" href="/images/logo.png" />
                </Head>`;
  if (s.includes('<Head>')) {
    // merge into existing Head if present
    s = s.replace(
      /<Head>\s*<title>Greenlight<\/title>\s*<\/Head>/,
      `<Head>
                <title>Greenlight</title>
                <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
                <link rel="manifest" href="/manifest.webmanifest" />
                <meta name="theme-color" content="#107C10" />
                <meta name="mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
                <link rel="apple-touch-icon" href="/images/logo.png" />
            </Head>`
    );
  } else if (s.includes('<UserProvider')) {
    s = s.replace('<UserProvider', headBlock + '\n            <UserProvider');
  } else {
    s = s.replace(/return\s*\(\s*/, 'return (\n            <>\n' + headBlock + '\n');
  }
  fs.writeFileSync(p, s);
  console.log('_app.tsx PWA + viewport injected');
}
EOF

RUN npm i --legacy-peer-deps \
 && npx next build renderer \
 && npx next export -o app renderer \
 && npm i tsx typescript --no-save \
 && (cd node_modules/xal-node && npm i && npm run build || true)

# ---------- runtime ----------
FROM node:18-alpine

ARG BUILD_ARCH=amd64
ARG BUILD_VERSION=2.3.2
ARG BUILD_DATE

LABEL \
  io.hass.name="Greenlight" \
  io.hass.description="Xbox xCloud & Home streaming WebUI" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.title="Greenlight" \
  org.opencontainers.image.description="Open-source Xbox streaming client for Home Assistant" \
  org.opencontainers.image.source="https://github.com/pccr10001/greenlight-webonly" \
  org.opencontainers.image.version="${BUILD_VERSION}" \
  org.opencontainers.image.created="${BUILD_DATE}"

WORKDIR /app

RUN apk add --no-cache bash jq curl tini \
 && npm install -g tsx

COPY --from=builder /app /app
COPY rootfs/run.sh /run.sh
COPY rootfs/default-manifest.webmanifest /app/app/manifest.webmanifest

RUN chmod a+x /run.sh \
 && mkdir -p /data \
 && ln -sfn /data /app/data

EXPOSE 9003

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/run.sh"]
