#!/usr/bin/env python3
"""Mirror SDUI cloud files to a local directory for SMB."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse

import requests

API = "https://api.sdui.app/v1"
LOG = logging.getLogger("sdui-sync")

DATA_DIR = Path(os.environ.get("SDUI_DATA", "/data"))
SHARE_DIR = Path(os.environ.get("SDUI_SHARE", "/share/sdui-cloud"))
STATE_FILE = DATA_DIR / "sync_state.json"
TOKEN_FILE = DATA_DIR / "auth.json"
CONFIG_FILE = Path(os.environ.get("SDUI_CONFIG", "/data/options.json"))


def load_options() -> dict[str, Any]:
    """Load add-on options from JSON config."""
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {
        "school_slink": os.environ.get("SDUI_SLINK", ""),
        "school_search": os.environ.get("SDUI_SEARCH", ""),
        "username": os.environ.get("SDUI_USERNAME", ""),
        "password": os.environ.get("SDUI_PASSWORD", ""),
        "bearer_token": os.environ.get("SDUI_TOKEN", ""),
        "user_id": os.environ.get("SDUI_USER_ID", ""),
        "sync_interval_minutes": int(os.environ.get("SDUI_INTERVAL", "30")),
        "only_cloud_ids": [],
        "max_file_size_mb": 500,
        "download_concurrency": 4,
    }


def safe_name(name: str) -> str:
    """Sanitize a path segment for local filesystems."""
    name = name.strip() or "unnamed"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name)
    name = name.rstrip(" .")
    return name[:200] or "unnamed"


def load_auth() -> dict[str, Any]:
    """Read cached token file."""
    if TOKEN_FILE.exists():
        try:
            return json.loads(TOKEN_FILE.read_text())
        except Exception:
            pass
    return {}


def save_auth(auth: dict[str, Any]) -> None:
    """Persist token cache atomically."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = TOKEN_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(auth, indent=2))
    tmp.replace(TOKEN_FILE)


def token_still_valid(auth: dict[str, Any], skew: int = 300) -> bool:
    """True if access token is still usable."""
    exp = auth.get("expires_at")
    if not exp or not auth.get("access_token"):
        return False
    return time.time() < float(exp) - skew


def decode_jwt_sub(token: str) -> str | None:
    """Extract user id from JWT payload."""
    try:
        import base64

        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        data = json.loads(base64.urlsafe_b64decode(payload))
        return str(data.get("sub") or "") or None
    except Exception:
        return None


class SduiLoginError(Exception):
    """Authentication or school resolution failed."""


def search_school_slink(session: requests.Session, query: str) -> str:
    """Resolve school_search to the first matching slink."""
    r = session.get(f"{API}/leads", params={"search": query}, timeout=30)
    r.raise_for_status()
    hits = r.json().get("data") or []
    if not hits:
        raise SduiLoginError(f"no school found for search={query!r}")
    first = hits[0]
    slink = first.get("slink")
    if not slink:
        raise SduiLoginError(f"first search hit has no slink: {first!r}")
    LOG.info(
        "school search %r → %s (%s)",
        query,
        first.get("name") or slink,
        slink,
    )
    if len(hits) > 1:
        LOG.info("%s further hit(s) ignored (using first only)", len(hits) - 1)
    return str(slink)


def find_school(session: requests.Session, slink: str) -> dict:
    """Load school metadata by exact slink."""
    r = session.get(f"{API}/find-schools", params={"slink": slink}, timeout=30)
    r.raise_for_status()
    data = r.json().get("data")
    if not data:
        raise SduiLoginError(f"school not found for slink={slink}")
    return data


def resolve_school_slink(session: requests.Session, opts: dict[str, Any]) -> str:
    """Prefer school_slink; otherwise search and take first result."""
    slink = (opts.get("school_slink") or "").strip()
    if slink:
        return slink
    query = (opts.get("school_search") or "").strip()
    if query:
        return search_school_slink(session, query)
    raise SduiLoginError("set school_slink or school_search")


def _is_uuid(value: str) -> bool:
    """True if value looks like a UUID."""
    return bool(
        re.fullmatch(
            r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
            value or "",
        )
    )


def _collect_redirect_urls(resp: requests.Response) -> list[str]:
    """Collect URLs from history, Location headers and final URL."""
    urls: list[str] = []
    for hist in resp.history:
        loc = hist.headers.get("Location") or ""
        if loc:
            urls.append(urljoin(hist.url, loc))
        urls.append(hist.url)
    urls.append(resp.url)
    return urls


def login_webuntis(school_slink: str, username: str, password: str) -> dict[str, Any]:
    """WebUntis SSO → SDUI bearer token."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "de-DE,de;q=0.9",
        }
    )

    school = find_school(session, school_slink)
    providers = (school.get("meta") or {}).get("external_identity_providers") or []
    if not providers:
        raise SduiLoginError(
            "school has no external identity provider (WebUntis required)"
        )

    idp_base = providers[0]["uri"]
    app_state = json.dumps(
        {
            "branding": "DEFAULT",
            "slink": school_slink,
            "goBackToParentWindow": False,
        },
        separators=(",", ":"),
    )
    redirect_uri = f"https://sdui.app/sso-verify/{school_slink}"
    if "?" in idp_base:
        idp_url = idp_base
    else:
        idp_url = f"{idp_base}?client_id=sdui"
    if "client_id=" not in idp_url:
        idp_url += f"{'&' if '?' in idp_url else '?'}client_id=sdui"
    if "redirect_uri=" not in idp_url:
        idp_url += f"&redirect_uri={requests.utils.quote(redirect_uri, safe='')}"
    idp_url += f"&state={requests.utils.quote(app_state, safe='')}"

    LOG.info("IDP auth for %s", school.get("name") or school_slink)
    r = session.get(idp_url, timeout=30, allow_redirects=True)
    r.raise_for_status()

    # Parse WebUntis authorize URL from IDP HTML
    webuntis_auth = None
    m = re.search(r'window\.top\.location\.href\s*=\s*"([^"]+)"', r.text or "")
    if not m:
        m = re.search(r"url=(https://[^'\"\s>]+)", r.text or "")
    if m:
        webuntis_auth = m.group(1).replace("\\/", "/")
    if not webuntis_auth and "webuntis.com" in r.url:
        webuntis_auth = r.url
    if not webuntis_auth:
        raise SduiLoginError("missing WebUntis authorize URL from IDP")

    # Keep authorize URL with PKCE params for post-login replay
    authorize_url = webuntis_auth

    LOG.info("WebUntis authorize")
    r = session.get(authorize_url, timeout=30, allow_redirects=True)
    r.raise_for_status()

    login_url = urljoin(r.url, "/WebUntis/j_spring_security_check")
    parsed = urlparse(r.url)
    qs = parse_qs(parsed.query)
    school_param = qs.get("school", [""])[0]
    if not school_param:
        host = parsed.hostname or ""
        if host.endswith(".webuntis.com"):
            school_param = host.split(".")[0]
    if not school_param:
        school_param = school_slink.split("-")[0]

    LOG.info("WebUntis login school=%s user=%s", school_param, username)
    r = session.post(
        login_url,
        data={
            "school": school_param,
            "j_username": username,
            "j_password": password,
            "token": "",
        },
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": f"{parsed.scheme}://{parsed.hostname}",
            "Referer": r.url,
        },
        timeout=30,
        allow_redirects=True,
    )

    wu_code = None
    wu_state = None
    sdui_code = None

    def ingest(url: str) -> None:
        nonlocal wu_code, wu_state, sdui_code
        if not url:
            return
        q = parse_qs(urlparse(url).query)
        code = (q.get("code") or [None])[0]
        state = (q.get("state") or [None])[0]
        if state and not str(state).startswith("{"):
            wu_state = state
        if not code:
            return
        if _is_uuid(code) or "sso-verify" in url or "idp.sdui.app" in url:
            # SDUI app code is UUID-shaped
            if _is_uuid(code):
                sdui_code = code
            elif "sso-verify" in url:
                sdui_code = code
        else:
            wu_code = code

    for u in _collect_redirect_urls(r):
        ingest(u)

    # Replay authorize if login did not already yield a code
    if not wu_code and not sdui_code:
        LOG.info("re-authorize after login")
        r2 = session.get(authorize_url, timeout=30, allow_redirects=True)
        for u in _collect_redirect_urls(r2):
            ingest(u)

    # Browser hits sdui.app/webuntis then IDP return exchanges the code
    if wu_code and not sdui_code:
        LOG.info("exchange WebUntis code at IDP")
        # Match SPA behaviour: open webuntis callback then IDP return
        session.get(
            "https://sdui.app/webuntis",
            params={"code": wu_code, "state": wu_state or ""},
            timeout=30,
            allow_redirects=True,
        )
        r3 = session.get(
            "https://idp.sdui.app/api/auth/return",
            params={"code": wu_code, "state": wu_state or ""},
            timeout=30,
            allow_redirects=False,
        )
        loc = r3.headers.get("Location") or ""
        if loc:
            ingest(urljoin(r3.url, loc))
        # Follow once if needed
        if not sdui_code and loc:
            r4 = session.get(urljoin(r3.url, loc), timeout=30, allow_redirects=True)
            for u in _collect_redirect_urls(r4):
                ingest(u)
        if not sdui_code and r3.status_code >= 400:
            raise SduiLoginError(
                f"IDP return failed: {r3.status_code} {(r3.text or '')[:200]}"
            )

    if not sdui_code:
        raise SduiLoginError(
            "no SDUI auth code – check credentials / WebUntis school"
        )

    if not _is_uuid(sdui_code):
        LOG.warning("SDUI code is not UUID-shaped, trying login-idm anyway")

    def do_login_idm(native: bool) -> requests.Response:
        params = {"is_native": "true"} if native else {}
        return session.post(
            f"{API}/auth/login-idm",
            params=params,
            json={"slink": school_slink, "code": sdui_code},
            headers={
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Origin": "https://sdui.app",
                "Referer": f"https://sdui.app/sso-verify/{school_slink}",
                "frontend-version": "2025.1.0@addon",
                "released-at": "2026-11-25 16:07:42",
            },
            timeout=30,
        )

    LOG.info("login-idm token exchange")
    r_login = do_login_idm(True)
    if r_login.status_code >= 400:
        LOG.warning("login-idm native failed (%s), retry without is_native", r_login.status_code)
        r_login = do_login_idm(False)
    if r_login.status_code >= 400:
        raise SduiLoginError(
            f"login-idm failed: {r_login.status_code} {r_login.text[:300]}"
        )
    body = r_login.json().get("data") or {}
    access = body.get("access_token")
    if not access:
        raise SduiLoginError("login-idm returned no access_token")

    expires_in = int(body.get("expires_in") or 2592000)
    user_id = decode_jwt_sub(access)
    auth = {
        "access_token": access,
        "token_type": body.get("token_type") or "Bearer",
        "expires_in": expires_in,
        "expires_at": time.time() + expires_in,
        "user_id": user_id,
        "school_slink": school_slink,
        "obtained_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    for c in session.cookies:
        if c.name.startswith("refresh_token"):
            auth["refresh_cookie_name"] = c.name
            auth["refresh_cookie_value"] = c.value
            break
    save_auth(auth)
    LOG.info("login ok user_id=%s expires_in=%ss", user_id, expires_in)
    return auth


def ensure_auth(opts: dict[str, Any]) -> dict[str, Any]:
    """Return a valid auth dict; login when needed."""
    auth = load_auth()
    if token_still_valid(auth):
        return auth

    manual = (opts.get("bearer_token") or "").strip()
    if manual:
        user_id = (opts.get("user_id") or "").strip() or decode_jwt_sub(manual)
        auth = {
            "access_token": manual,
            "user_id": user_id,
            "expires_at": time.time() + 86400 * 25,
            "source": "manual",
        }
        save_auth(auth)
        return auth

    user = (opts.get("username") or "").strip()
    password = opts.get("password") or ""
    if not (user and password):
        raise SduiLoginError(
            "need username + password and school_slink/school_search "
            "(or bearer_token)"
        )

    session = requests.Session()
    session.headers.update({"Accept": "application/json", "User-Agent": "SduiCloudSync/1.2"})
    slink = resolve_school_slink(session, opts)
    return login_webuntis(slink, user, password)


class SduiClient:
    """Thin authenticated SDUI REST client."""

    def __init__(self, token: str, user_id: str):
        self.user_id = str(user_id)
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/json",
                "User-Agent": "SduiCloudSync/1.2 (HomeAssistant)",
                "frontend-version": "2025.1.0@addon",
                "released-at": "2026-11-24 18:02:14",
            }
        )

    def get(self, path: str, params: dict | None = None) -> Any:
        url = path if path.startswith("http") else f"{API}{path}"
        r = self.session.get(url, params=params, timeout=60)
        if r.status_code == 401:
            raise SduiLoginError("token rejected (401)")
        r.raise_for_status()
        if not r.content:
            return None
        return r.json()

    def list_clouds(self) -> list[dict]:
        clouds = []
        page = 1
        while True:
            data = self.get(
                f"/users/{self.user_id}/channels/clouds",
                {"page": page, "search": ""},
            )
            batch = data.get("data") or []
            if not batch:
                break
            clouds.extend(batch)
            page += 1
            if page > 50:
                break
        return clouds

    def list_files(
        self,
        cloud_id: int,
        parent_uuid: str | None = None,
        path: str = "",
    ) -> list[dict]:
        items: list[dict] = []
        page = 1
        file_param = parent_uuid or ""
        while True:
            data = self.get(
                f"/channels/cloud/{cloud_id}/files",
                {
                    "file": file_param,
                    "path": path,
                    "order-by": "name",
                    "order-dir": "asc",
                    "file_type": "",
                    "limit": 50,
                    "page": page,
                    "search": "",
                },
            )
            batch = data.get("data") or []
            if not batch:
                break
            items.extend(batch)
            page += 1
            if page > 200:
                LOG.warning("cloud %s pagination stop at page %s", cloud_id, page)
                break
        return items

    def file_detail(self, cloud_id: int, uuid: str) -> dict:
        data = self.get(f"/channels/cloud/{cloud_id}/files/{uuid}")
        return data.get("data") or data


def load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"files": {}}


def save_state(state: dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=0))
    tmp.replace(STATE_FILE)


def download_file(url: str, dest: Path, expected_size: int | None = None) -> bool:
    """Download URL to dest via temp .part file."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(part, "wb") as f:
                for chunk in r.iter_content(1024 * 256):
                    if chunk:
                        f.write(chunk)
        if expected_size and part.stat().st_size != expected_size:
            LOG.warning(
                "size mismatch %s: got %s expected %s",
                dest.name,
                part.stat().st_size,
                expected_size,
            )
        part.replace(dest)
        return True
    except Exception as exc:
        LOG.error("download failed %s: %s", dest, exc)
        if part.exists():
            part.unlink(missing_ok=True)
        return False


def walk_cloud(
    client: SduiClient,
    cloud_id: int,
    parent_uuid: str | None,
    path_prefix: str,
    local_root: Path,
    max_bytes: int,
) -> list[dict]:
    """Recursively collect download jobs for one cloud."""
    jobs: list[dict] = []
    try:
        items = client.list_files(cloud_id, parent_uuid, path_prefix)
    except Exception as exc:
        LOG.error("list files cloud=%s parent=%s: %s", cloud_id, parent_uuid, exc)
        return jobs

    for item in items:
        name = safe_name(item.get("name") or item.get("alt_name") or "unnamed")
        ftype = item.get("file_type")
        uuid = item.get("uuid")
        if not uuid:
            continue

        if ftype == "DIR":
            sub_path = f"{path_prefix}/{name}".replace("//", "/")
            jobs.extend(
                walk_cloud(
                    client,
                    cloud_id,
                    uuid,
                    sub_path,
                    local_root / name,
                    max_bytes,
                )
            )
            continue

        if ftype != "FILE":
            continue

        size = int(item.get("size") or 0)
        if size > max_bytes:
            LOG.info("skip large file %s (%s MB)", name, size // (1024 * 1024))
            continue

        meta = item.get("meta") or {}
        download_uri = meta.get("download_uri") or meta.get("uri")
        if not download_uri or "s3." not in str(download_uri):
            try:
                detail = client.file_detail(cloud_id, uuid)
                meta = detail.get("meta") or meta
                download_uri = meta.get("download_uri") or meta.get("uri")
            except Exception as exc:
                LOG.warning("detail %s: %s", uuid, exc)
                continue

        if not download_uri or "s3." not in str(download_uri):
            continue

        jobs.append(
            {
                "uuid": uuid,
                "name": name,
                "size": size,
                "updated_at": item.get("updated_at") or item.get("created_at") or "",
                "local_path": str(local_root / name),
                "cloud_id": cloud_id,
                "download_uri": download_uri,
            }
        )
    return jobs


def run_sync(opts: dict[str, Any]) -> None:
    """One full authentication + mirror pass."""
    auth = ensure_auth(opts)
    token = auth["access_token"]
    user_id = str(auth.get("user_id") or opts.get("user_id") or "").strip()
    if not user_id:
        user_id = decode_jwt_sub(token) or ""
    if not user_id:
        raise SduiLoginError("user_id unknown")

    only = set(str(x) for x in (opts.get("only_cloud_ids") or []))
    max_bytes = int(opts.get("max_file_size_mb") or 500) * 1024 * 1024
    workers = int(opts.get("download_concurrency") or 4)

    client = SduiClient(token, user_id)
    state = load_state()
    known: dict[str, Any] = state.setdefault("files", {})

    LOG.info("listing clouds")
    try:
        clouds = client.list_clouds()
    except SduiLoginError:
        LOG.warning("token rejected – re-login")
        if TOKEN_FILE.exists():
            TOKEN_FILE.unlink()
        auth = ensure_auth(opts)
        client = SduiClient(auth["access_token"], str(auth.get("user_id") or user_id))
        clouds = client.list_clouds()

    LOG.info("%s cloud channel(s)", len(clouds))

    all_jobs: list[dict] = []
    for ch in clouds:
        cloud_id = ch.get("cloud_id")
        if not cloud_id:
            continue
        if only and str(cloud_id) not in only:
            continue
        display = safe_name(
            (ch.get("meta") or {}).get("displayname")
            or ch.get("name")
            or f"cloud-{cloud_id}"
        )
        local_root = SHARE_DIR / display
        local_root.mkdir(parents=True, exist_ok=True)
        LOG.info("scan %s (%s)", display, cloud_id)
        all_jobs.extend(
            walk_cloud(client, int(cloud_id), None, "", local_root, max_bytes)
        )

    LOG.info("%s file(s) listed", len(all_jobs))

    to_download: list[dict] = []
    seen_uuids: set[str] = set()
    for job in all_jobs:
        uid = job["uuid"]
        seen_uuids.add(uid)
        prev = known.get(uid)
        dest = Path(job["local_path"])
        if (
            prev
            and prev.get("updated_at") == job["updated_at"]
            and dest.exists()
            and dest.stat().st_size == job["size"]
        ):
            continue
        to_download.append(job)

    LOG.info("%s file(s) to download", len(to_download))
    ok = 0
    fail = 0

    def _one(job: dict) -> tuple[str, bool]:
        dest = Path(job["local_path"])
        success = download_file(job["download_uri"], dest, job["size"] or None)
        if not success:
            try:
                detail = client.file_detail(job["cloud_id"], job["uuid"])
                meta = detail.get("meta") or {}
                uri2 = meta.get("download_uri") or meta.get("uri")
                if uri2:
                    success = download_file(uri2, dest, job["size"] or None)
            except Exception as exc:
                LOG.error("url refresh %s: %s", job["name"], exc)
        return job["uuid"], success

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_one, j): j for j in to_download}
        for fut in as_completed(futures):
            job = futures[fut]
            try:
                uid, success = fut.result()
            except Exception as exc:
                LOG.error("job error: %s", exc)
                fail += 1
                continue
            if success:
                ok += 1
                known[uid] = {
                    "updated_at": job["updated_at"],
                    "size": job["size"],
                    "path": job["local_path"],
                    "name": job["name"],
                }
            else:
                fail += 1

    for u in [x for x in list(known.keys()) if x not in seen_uuids]:
        p = known[u].get("path")
        if p and Path(p).exists():
            try:
                Path(p).unlink()
                LOG.info("removed orphan %s", p)
            except OSError:
                pass
        known.pop(u, None)

    state["files"] = known
    state["last_sync"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    state["stats"] = {"downloaded": ok, "failed": fail, "total_tracked": len(known)}
    save_state(state)
    LOG.info("sync done downloaded=%s failed=%s tracked=%s", ok, fail, len(known))


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    opts = load_options()
    interval = max(5, int(opts.get("sync_interval_minutes") or 30)) * 60
    SHARE_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    once = "--once" in sys.argv
    while True:
        try:
            run_sync(opts)
        except SduiLoginError as e:
            LOG.error("auth: %s", e)
            if once:
                raise SystemExit(1)
            time.sleep(120)
            opts = load_options()
            continue
        except Exception:
            LOG.exception("sync crashed")
        if once:
            break
        LOG.info("next sync in %s min", interval // 60)
        time.sleep(interval)
        opts = load_options()


if __name__ == "__main__":
    main()
