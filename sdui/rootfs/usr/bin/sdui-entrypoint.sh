#!/usr/bin/env bash
# Start Samba then run the SDUI sync loop.
set -euo pipefail

OPTIONS=/data/options.json
SHARE_DIR=/share/sdui-cloud
DATA_DIR=/data

mkdir -p "$SHARE_DIR" "$DATA_DIR"

if [[ -f /config/options.json ]]; then
  cp /config/options.json "$OPTIONS" 2>/dev/null || true
fi
if [[ ! -f "$OPTIONS" ]]; then
  echo '{}' > "$OPTIONS"
fi

SMB_USER=$(jq -r '.smb_username // "sdui"' "$OPTIONS")
SMB_PASS=$(jq -r '.smb_password // "changeme"' "$OPTIONS")
SHARE_NAME=$(jq -r '.smb_share_name // "sdui-cloud"' "$OPTIONS")

if ! id "$SMB_USER" &>/dev/null; then
  adduser -D -H -s /sbin/nologin "$SMB_USER" || true
fi
echo -e "${SMB_PASS}\n${SMB_PASS}" | smbpasswd -a -s "$SMB_USER" || true

cat > /etc/samba/smb.conf <<EOFSMB
[global]
   workgroup = WORKGROUP
   server string = SDUI Cloud
   security = user
   map to guest = never
   load printers = no
   printing = bsd
   printcap name = /dev/null
   disable spoolss = yes
   server min protocol = SMB2
   server max protocol = SMB3
   log level = 1
   bind interfaces only = no
   smb ports = 445

[${SHARE_NAME}]
   path = ${SHARE_DIR}
   browseable = yes
   read only = yes
   valid users = ${SMB_USER}
   force user = root
   create mask = 0644
   directory mask = 0755
EOFSMB

nmbd -D || true
smbd -D
echo "SMB share ready: \\\\HOST\\${SHARE_NAME} user=${SMB_USER}"

export SDUI_DATA="$DATA_DIR"
export SDUI_SHARE="$SHARE_DIR"
export SDUI_CONFIG="$OPTIONS"

exec python3 /usr/bin/sdui-sync.py
