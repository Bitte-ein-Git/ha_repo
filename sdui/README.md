# Sdui SMB

Home Assistant add-on that mirrors **Sdui messenger cloud** files to a local folder and exposes them as a read-only **SMB share**.

![logo](logo.png)

## Features

- WebUntis SSO login (school search or direct `slink`)
- Optional manual bearer token
- Recursive cloud sync with change detection
- Read-only Samba share
- Token cache and automatic re-login on expiry / 401

## Requirements

- Home Assistant OS / Supervised
- SDUI account that uses **WebUntis** as identity provider  
  (or a valid API bearer token)

## Install

1. Add this repository in **Settings → Add-ons → Add-on Store → ⋮ → Repositories**:
   ```
   https://github.com/Bitte-ein-Git/ha_repo
   ```
2. Install **Sdui SMB**
3. Configure options and start the add-on
4. Open port **445** if you connect from another device

For local development without Supervisor, copy this folder under `/addons/` or use `run-local.sh`.

## Configuration

| Option | Description |
|--------|-------------|
| `school_search` | Free-text school search; **first hit** is used if `school_slink` is empty |
| `school_slink` | Exact school slug (overrides search) |
| `username` | WebUntis username |
| `password` | WebUntis password |
| `bearer_token` | Optional; skip SSO and use this JWT |
| `user_id` | Optional; taken from JWT when omitted |
| `sync_interval_minutes` | Full sync interval (default `30`) |
| `smb_username` / `smb_password` | SMB credentials |
| `smb_share_name` | Share name (default `sdui-cloud`) |
| `only_cloud_ids` | Limit sync to these cloud IDs; empty = all |
| `max_file_size_mb` | Skip larger files |
| `download_concurrency` | Parallel downloads |

### Example

```yaml
school_search: "Example School"
username: "student.name"
password: "secret"
sync_interval_minutes: 30
smb_username: sdui
smb_password: "choose-a-strong-password"
smb_share_name: sdui-cloud
```

Or pin a known slug:

```yaml
school_slink: "example-school-slug"
username: "student.name"
password: "secret"
```

## SMB access

```
\\<home-assistant-ip>\sdui-cloud
```

Linux example:

```bash
sudo mount -t cifs //HA-IP/sdui-cloud /mnt/sdui \
  -o username=sdui,password=...,vers=3.0
```

## Layout

```
/share/sdui-cloud/
  <Cloud display name>/
    folder/
      file.pdf
```

State and tokens live under `/data/` inside the add-on.

## How login works

Unofficial flow derived from the SDUI web client:

1. Resolve school via `/v1/leads?search=` or `/v1/find-schools?slink=`
2. Open external IdP URL from school metadata
3. Complete WebUntis form login
4. Exchange codes through SDUI IdP return + `/v1/auth/login-idm`
5. Cache bearer token (~30 days)

This is **not** an official SDUI API. It may break when SDUI changes auth.

## Local test (no HA)

```bash
cp options.example.json options.local.json
# edit credentials
./run-local.sh
```

## Security

- Prefer strong `smb_password`
- Keep `password` / `bearer_token` only in add-on secrets
- Share is **read-only**
- Do not commit `options.local.json` or `/data/auth.json`

## License

MIT — © Bitte-ein-Git

## Maintainers

GitHub org: [Bitte-ein-Git](https://github.com/Bitte-ein-Git)
