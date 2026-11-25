# Sdui SMB – Documentation

## School resolution

1. If `school_slink` is set → `GET /v1/find-schools?slink=…`
2. Else if `school_search` is set → `GET /v1/leads?search=…` and take **first** result’s `slink`
3. Else authentication fails with a clear error

## Auth modes

### A) WebUntis SSO (default)

Needs `username`, `password`, and either `school_slink` or `school_search`.

### B) Static token

Set `bearer_token` (and optionally `user_id`). SSO options are ignored while the token is valid.

On HTTP 401 the add-on clears the cache and retries (SSO if configured).

## Sync behaviour

- Lists all channel clouds for the user (or `only_cloud_ids`)
- Walks folders recursively (`file_type` DIR / FILE)
- Downloads via short-lived S3 URLs from file metadata
- Skips unchanged files (uuid + `updated_at` + size)
- Removes local orphans no longer present upstream

## Networking

| Port | Use |
|------|-----|
| 445/tcp | SMB |
| 139/tcp | NetBIOS (legacy) |

Outbound HTTPS to `api.sdui.app`, `idp.sdui.app`, `*.webuntis.com`, and SDUI S3 endpoints is required.

## Limitations

- Read-only mirror (no upload/rename/delete back to SDUI)
- WebUntis IdP only (other school IdPs are not implemented)
- Unofficial API surface
- Protected folders without download permission are skipped

## Troubleshooting

| Symptom | Check |
|---------|--------|
| `school not found` | Adjust `school_search` / `school_slink` |
| `no SDUI auth code` | Username/password, WebUntis availability |
| `token rejected (401)` | Re-login; token expired |
| Empty share | User has no cloud files; check `only_cloud_ids` |
| SMB connect fail | Port 445, credentials, client SMB3 support |

Logs: Supervisor → Add-on → Log.


## Auth troubleshooting

| Log message | Meaning |
|-------------|---------|
| `no SDUI auth code` | WebUntis login or authorize redirect failed |
| `login-idm failed: 400` / user not found | Code exchange produced no linked SDUI user – confirm WebUntis user works on sdui.app, or use `bearer_token` |
| `token rejected (401)` | Cached token expired – re-login runs automatically |
