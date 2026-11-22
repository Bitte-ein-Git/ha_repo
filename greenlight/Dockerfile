ARG BUILD_FROM
FROM node:18-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git python3 make g++

ARG GREENLIGHT_REF=main-v2
RUN git clone --depth 1 -b ${GREENLIGHT_REF} https://github.com/pccr10001/greenlight-webonly.git .

# ESLint/TS must not fail HA image builds
RUN node <<'EOF'
const fs = require('fs');
const path = 'renderer/next.config.js';
if (fs.existsSync(path)) {
  let conf = fs.readFileSync(path, 'utf8');
  if (!conf.includes('ignoreDuringBuilds')) {
    conf = conf.replace(
      /module\.exports\s*=\s*\{/,
      "module.exports = {\n  eslint: { ignoreDuringBuilds: true },\n  typescript: { ignoreBuildErrors: true },"
    );
    fs.writeFileSync(path, conf);
  }
} else {
  fs.writeFileSync(path, `module.exports = {
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
};
`);
}
console.log('next.config.js ready');
EOF

# HA plumbing only (port / secret / optional PWA manifest route) — used by stock + mobile
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
        // PWA manifest (optional; written by /run.sh when not using unmodified UI)
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
console.log('webui.ts HA patch applied');
EOF

RUN npm i --legacy-peer-deps \
 && npm i tsx typescript --no-save \
 && (cd node_modules/xal-node && npm i && npm run build || true)

# --- STOCK WebUI (no UI modifications) ---
RUN npx next build renderer \
 && npx next export -o app-stock renderer \
 && echo "stock export done" \
 && ls -la app-stock | head

# --- MOBILE / RemotePlay UI patches ---
COPY rootfs/mobile.css renderer/mobile.css
COPY rootfs/header.mobile.tsx renderer/components/header.tsx
COPY rootfs/home.mobile.tsx renderer/pages/home.tsx
COPY rootfs/default-manifest.webmanifest renderer/public/manifest.webmanifest

RUN echo '' >> renderer/styles.css \
 && echo '/* Mobile / RemotePlay (HA addon) */' >> renderer/styles.css \
 && echo "@import 'mobile.css';" >> renderer/styles.css

RUN node <<'EOF'
const fs = require('fs');
const p = 'renderer/pages/_app.tsx';
let s = fs.readFileSync(p, 'utf8');

const headInner = `
                <title>RemotePlay</title>
                <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, maximum-scale=1, user-scalable=no" />
                <link rel="manifest" href="/manifest.webmanifest" />
                <meta name="theme-color" content="#107C10" />
                <meta name="mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
                <meta name="apple-mobile-web-app-title" content="RemotePlay" />
                <link rel="apple-touch-icon" href="/images/logo.png" />
                <link rel="apple-touch-startup-image" href="/images/logo.png" />
`;

if (s.includes('<Head>')) {
  s = s.replace(/<Head>[\s\S]*?<\/Head>/, `<Head>${headInner}</Head>`);
} else if (s.includes('<UserProvider')) {
  s = s.replace('<UserProvider', `<Head>${headInner}</Head>\n            <UserProvider`);
}

s = s.replace(/<div id="app_sidebar"[\s\S]*?<\/div>\s*<Footer \/>/, '<Footer />');
s = s.replace(/import SidebarFriends from[^\n]+\n/, '');
s = s.replace(/<SidebarFriends><\/SidebarFriends>/g, '');

if (!s.includes('rp-streaming')) {
  s = s.replace(
    'const router = useRouter()',
    `const router = useRouter()
    React.useEffect(() => {
        if (typeof document === 'undefined') return
        const onStream = (router.pathname || '').startsWith('/stream')
        document.body.classList.toggle('rp-streaming', onStream)
        return () => document.body.classList.remove('rp-streaming')
    }, [router.pathname])`
  );
}

fs.writeFileSync(p, s);
console.log('_app.tsx mobile patched');
EOF

RUN node <<'EOF'
const fs = require('fs');
const p = 'renderer/pages/stream/[serverid].tsx';
let s = fs.readFileSync(p, 'utf8');

if (!s.includes('mediaSession')) {
  s = s.replace(/Greenlight - Streaming/g, 'RemotePlay –');
  const anchor = "const [queueTime, setQueueTime] = React.useState(0)";
  const hook = `const [queueTime, setQueueTime] = React.useState(0)

    React.useEffect(() => {
        if (typeof navigator === 'undefined' || !('mediaSession' in navigator)) return
        const serverId = String(router.query.serverid || 'Console')
        const nameQ = router.query.name
        const isCloud = serverId.substring(0, 6) === 'xcloud'
        const title = isCloud ? 'xCloud' : (Array.isArray(nameQ) ? nameQ[0] : (nameQ || serverId))
        try {
            navigator.mediaSession.metadata = new MediaMetadata({
                title: title,
                artist: 'Remote Play',
                album: 'Xbox',
                artwork: [
                    { src: '/images/logo.png', sizes: '192x192', type: 'image/png' },
                    { src: '/images/logo.png', sizes: '512x512', type: 'image/png' },
                ],
            })
            navigator.mediaSession.playbackState = 'playing'
        } catch (e) {
            console.log('MediaSession setup failed', e)
        }
        return () => {
            try {
                navigator.mediaSession.playbackState = 'none'
                navigator.mediaSession.metadata = null
            } catch (e) {
                console.log('MediaSession cleanup', e)
            }
        }
    }, [router.query.serverid, router.query.name])`;
  if (s.includes(anchor)) s = s.replace(anchor, hook);
}
fs.writeFileSync(p, s);
console.log('stream media session patched');
EOF

RUN node <<'EOF'
const fs = require('fs');
const p = 'renderer/components/settings/sidebar.tsx';
if (fs.existsSync(p)) {
  let s = fs.readFileSync(p, 'utf8');
  s = s.replace('>About<', '>Account<');
  fs.writeFileSync(p, s);
}
EOF

RUN npx next build renderer \
 && npx next export -o app-mobile renderer \
 && echo "mobile export done" \
 && ls -la app-mobile | head

# Default active tree = stock (safe; black-screen fix). run.sh may switch.
RUN rm -rf app && cp -a app-stock app

# ---------- runtime ----------
FROM node:18-alpine

ARG BUILD_ARCH=amd64
ARG BUILD_VERSION=1.3.0
ARG BUILD_DATE

LABEL \
  io.hass.name="RemotePlay" \
  io.hass.description="Xbox Remote Play WebUI for Home Assistant" \
  io.hass.version="${BUILD_VERSION}" \
  io.hass.type="addon" \
  io.hass.arch="${BUILD_ARCH}" \
  org.opencontainers.image.title="RemotePlay" \
  org.opencontainers.image.description="Open-source Xbox Remote Play client for Home Assistant" \
  org.opencontainers.image.source="https://github.com/pccr10001/greenlight-webonly" \
  org.opencontainers.image.version="${BUILD_VERSION}" \
  org.opencontainers.image.created="${BUILD_DATE}"

WORKDIR /app

RUN apk add --no-cache bash jq curl tini \
 && npm install -g tsx

COPY --from=builder /app /app
COPY rootfs/run.sh /run.sh
COPY rootfs/default-manifest.webmanifest /app/app-mobile/manifest.webmanifest

RUN chmod a+x /run.sh \
 && mkdir -p /data \
 && ln -sfn /data /app/data \
 && test -d /app/app-stock \
 && test -d /app/app-mobile

EXPOSE 9003

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/run.sh"]
