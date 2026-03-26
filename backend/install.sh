#!/bin/bash
# WiFi Monitor Backend Installation Script
# For Debian/Ubuntu-based Linux servers (including Raspberry Pi)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/wifi-monitor-backend"
SERVICE_NAME="wifi-monitor-backend"
SERVICE_USER="wifi-monitor"
APP_PORT=5000
WORKERS=4

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  WiFi Monitor Backend Installation    ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}✗ Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}This script will:${NC}"
echo "  • Install system dependencies (Python 3, PostgreSQL client libs)"
echo "  • Create a dedicated service user account"
echo "  • Install Python dependencies into a virtual environment"
echo "  • Copy application files to $INSTALL_DIR"
echo "  • Set up the environment configuration file"
echo "  • Install and enable a systemd service (Gunicorn)"
echo "  • Configure log rotation"
echo ""
read -p "Continue with installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled"
    exit 0
fi

# ---------------------------------------------------------------------------
# [1/8] System packages
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}[1/8] Updating system packages...${NC}"
apt-get update -qq

echo -e "\n${GREEN}[2/8] Installing system dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    libpq-dev \
    gcc \
    git \
    curl

# ---------------------------------------------------------------------------
# [3/8] Service user
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}[3/8] Creating service user...${NC}"
if id "$SERVICE_USER" &>/dev/null; then
    echo "  User '$SERVICE_USER' already exists"
else
    useradd -r -s /bin/false -d "$INSTALL_DIR" -M "$SERVICE_USER"
    echo "  Created system user '$SERVICE_USER'"
fi

# ---------------------------------------------------------------------------
# [4/8] Application files
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}[4/8] Setting up installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"
mkdir -p "$INSTALL_DIR/instance"
mkdir -p "$INSTALL_DIR/config"

echo "  Copying application files..."
cp -r app         "$INSTALL_DIR/"
cp    run.py      "$INSTALL_DIR/"
cp    requirements.txt "$INSTALL_DIR/"

# Copy env file if it doesn't exist yet
ENV_FILE="$INSTALL_DIR/config/.env"
if [ ! -f "$ENV_FILE" ]; then
    # Try to find the repo-level .env.example
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    EXAMPLE="$SCRIPT_DIR/../config/.env.example"
    if [ -f "$EXAMPLE" ]; then
        cp "$EXAMPLE" "$ENV_FILE"
        echo "  Created $ENV_FILE from .env.example — please edit it before starting the service"
    else
        cat > "$ENV_FILE" << 'ENVEOF'
DATABASE_URL=sqlite:///wifi_monitor.db
SECRET_KEY=change_me
JWT_SECRET_KEY=change_me_jwt
FLASK_ENV=production
CORS_ORIGINS=*
ENVEOF
        echo "  Created default $ENV_FILE — please edit it before starting the service"
    fi
else
    echo "  Config file $ENV_FILE already exists, skipping"
fi

# Restrict permissions on .env
chmod 600 "$ENV_FILE"

# Set ownership
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 775 "$INSTALL_DIR/logs"
chmod 775 "$INSTALL_DIR/instance"

# ---------------------------------------------------------------------------
# [5/8] Python virtual environment & dependencies
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}[5/8] Installing Python dependencies...${NC}"
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"
echo "  Created virtual environment"

sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q
echo "  Installed Python packages"

# ---------------------------------------------------------------------------
# [6/8] Database migrations (optional — run manually if using PostgreSQL)
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}[6/8] Skipping automatic database migrations${NC}"
echo "  Run migrations manually after configuring $ENV_FILE:"
echo "    cd $INSTALL_DIR && BACKEND_ENV_FILE=$ENV_FILE venv/bin/flask --app app.wsgi:app db upgrade"

# ---------------------------------------------------------------------------
# [7/8] Systemd service
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}[7/8] Installing systemd service...${NC}"
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=WiFi Monitor Backend (Gunicorn)
After=network.target

[Service]
Type=simple
User=$SERVICE_USER
Group=$SERVICE_USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="BACKEND_ENV_FILE=$ENV_FILE"
ExecStart=$INSTALL_DIR/venv/bin/gunicorn \
    --workers $WORKERS \
    --bind 0.0.0.0:$APP_PORT \
    --access-logfile $INSTALL_DIR/logs/access.log \
    --error-logfile  $INSTALL_DIR/logs/error.log \
    --log-level info \
    app.wsgi:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/logs $INSTALL_DIR/instance

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
echo "  Installed and enabled systemd service '$SERVICE_NAME'"

# ---------------------------------------------------------------------------
# [8/8] Log rotation
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}[8/8] Configuring log rotation...${NC}"
cat > "/etc/logrotate.d/$SERVICE_NAME" << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $SERVICE_USER $SERVICE_USER
    postrotate
        systemctl kill -s USR1 $SERVICE_NAME 2>/dev/null || true
    endscript
}
EOF
echo "  Configured log rotation"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      Installation Complete! 🎉         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Edit the environment configuration:"
echo -e "   ${GREEN}nano $ENV_FILE${NC}"
echo ""
echo "   Key settings:"
echo "     • DATABASE_URL  — PostgreSQL or SQLite connection string"
echo "     • SECRET_KEY    — Random secret (use: openssl rand -hex 32)"
echo "     • JWT_SECRET_KEY — Random secret (use: openssl rand -hex 32)"
echo "     • CORS_ORIGINS  — Allowed frontend origins"
echo ""
echo "2. (If using PostgreSQL) Run database migrations:"
echo -e "   ${GREEN}cd $INSTALL_DIR && BACKEND_ENV_FILE=$ENV_FILE venv/bin/flask --app app.wsgi:app db upgrade${NC}"
echo ""
echo "3. Start the service:"
echo -e "   ${GREEN}systemctl start $SERVICE_NAME${NC}"
echo ""
echo "4. Check service status:"
echo -e "   ${GREEN}systemctl status $SERVICE_NAME${NC}"
echo ""
echo "5. View logs:"
echo -e "   ${GREEN}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "   ${GREEN}tail -f $INSTALL_DIR/logs/error.log${NC}"
echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "  • If gunicorn fails to bind, check that port $APP_PORT is free"
echo "  • Verify DATABASE_URL is correct and the DB is reachable"
echo "  • Check $INSTALL_DIR/logs/error.log for application errors"
echo ""
echo -e "${GREEN}Installation location: $INSTALL_DIR${NC}"
echo -e "${GREEN}Service user:         $SERVICE_USER${NC}"
echo -e "${GREEN}Listening on port:    $APP_PORT${NC}"
echo -e "${GREEN}Gunicorn workers:     $WORKERS${NC}"
echo ""
