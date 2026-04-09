#!/usr/bin/env bash
set -euo pipefail

# Create and enable systemd services for pi-agent, backend, and admin-frontend.
# Run with sudo: sudo ./setup_services.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

AGENT_DIR="$ROOT_DIR/pi-agent"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/admin-frontend"

SERVICE_USER="${SUDO_USER:-$USER}"
SERVICE_GROUP="$SERVICE_USER"

if [[ "$EUID" -ne 0 ]]; then
  echo "ERROR: This script must be run as root (use sudo)." >&2
  exit 1
fi

AGENT_PY="/usr/bin/python3"
if [[ -x "$AGENT_DIR/venv/bin/python" ]]; then
  AGENT_PY="$AGENT_DIR/venv/bin/python"
fi

BACKEND_PY="/usr/bin/python3"
if [[ -x "$BACKEND_DIR/venv/bin/python" ]]; then
  BACKEND_PY="$BACKEND_DIR/venv/bin/python"
fi

BACKEND_ENV_FILE="$ROOT_DIR/config/.env"
BACKEND_ENV_LINE=""
if [[ -f "$BACKEND_ENV_FILE" ]]; then
  BACKEND_ENV_LINE="Environment=BACKEND_ENV_FILE=$BACKEND_ENV_FILE"
fi

cat > /etc/systemd/system/wifi-monitor-agent.service << EOF
[Unit]
Description=WiFi Monitor Pi Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$AGENT_DIR
Environment="PATH=$AGENT_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$AGENT_PY $AGENT_DIR/run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wifi-monitor-agent

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/wifi-monitor-backend.service << EOF
[Unit]
Description=WiFi Monitor Backend
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
$BACKEND_ENV_LINE
ExecStart=$BACKEND_PY $BACKEND_DIR/run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wifi-monitor-backend

[Install]
WantedBy=multi-user.target
EOF

cat > /etc/systemd/system/wifi-monitor-frontend.service << EOF
[Unit]
Description=WiFi Monitor Admin Frontend (Next.js dev server)
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_GROUP
WorkingDirectory=$FRONTEND_DIR
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="NODE_ENV=development"
ExecStart=/usr/bin/npm run dev -- --hostname 0.0.0.0 --port 3000
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wifi-monitor-frontend

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now wifi-monitor-agent.service
systemctl enable --now wifi-monitor-backend.service
systemctl enable --now wifi-monitor-frontend.service

echo "Services installed and started:"
systemctl status --no-pager wifi-monitor-agent.service wifi-monitor-backend.service wifi-monitor-frontend.service || true
