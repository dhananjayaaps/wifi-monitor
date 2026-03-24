#!/bin/bash
# WiFi Monitor Pi Agent Installation Script
# For Raspberry Pi running Raspberry Pi OS (Debian-based)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/wifi-monitor"
SERVICE_NAME="wifi-monitor"
USER="wifi-monitor"

echo -e "${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  WiFi Monitor Pi Agent Installation   ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root (use sudo)${NC}"
    exit 1
fi

echo -e "${YELLOW}This script will:${NC}"
echo "  • Install system dependencies"
echo "  • Create dedicated user account"
echo "  • Install Python dependencies"
echo "  • Configure network monitoring tools"
echo "  • Set up systemd service"
echo "  • Configure log rotation"
echo ""
read -p "Continue with installation? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled"
    exit 0
fi

# Update system
echo -e "\n${GREEN}[1/8] Updating system packages...${NC}"
apt-get update -qq

# Install system dependencies
echo -e "\n${GREEN}[2/8] Installing system dependencies...${NC}"
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    arp-scan \
    nmap \
    iptables \
    net-tools \
    iproute2 \
    git \
    curl

# Create user if doesn't exist
echo -e "\n${GREEN}[3/8] Creating service user...${NC}"
if id "$USER" &>/dev/null; then
    echo "  User '$USER' already exists"
else
    useradd -r -s /bin/bash -d "$INSTALL_DIR" -m "$USER"
    echo "  Created user '$USER'"
fi

# Create installation directory
echo -e "\n${GREEN}[4/8] Setting up installation directory...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/logs"

# Copy files
echo "  Copying application files..."
cp -r src "$INSTALL_DIR/"
cp run.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp config.yaml "$INSTALL_DIR/config.yaml.example"

# Create config if doesn't exist
if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
    cp config.yaml "$INSTALL_DIR/config.yaml"
    echo "  Created default config.yaml"
else
    echo "  Config file already exists, skipping"
fi

# Set permissions
chown -R "$USER:$USER" "$INSTALL_DIR"
chmod 755 "$INSTALL_DIR"
chmod 775 "$INSTALL_DIR/logs"

# Install Python dependencies
echo -e "\n${GREEN}[5/8] Installing Python dependencies...${NC}"
cd "$INSTALL_DIR"

# Create virtual environment
sudo -u "$USER" python3 -m venv venv
echo "  Created virtual environment"

# Activate and install packages
sudo -u "$USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip -q
sudo -u "$USER" "$INSTALL_DIR/venv/bin/pip" install -r requirements.txt -q
echo "  Installed Python packages"

# Configure sudo permissions for network tools
echo -e "\n${GREEN}[6/8] Configuring network tool permissions...${NC}"
SUDOERS_FILE="/etc/sudoers.d/wifi-monitor"
cat > "$SUDOERS_FILE" << EOF
# Allow wifi-monitor user to run network monitoring tools without password
$USER ALL=(ALL) NOPASSWD: /usr/bin/arp-scan
$USER ALL=(ALL) NOPASSWD: /usr/sbin/arp-scan
$USER ALL=(ALL) NOPASSWD: /usr/bin/nmap
$USER ALL=(ALL) NOPASSWD: /usr/sbin/iptables
$USER ALL=(ALL) NOPASSWD: /sbin/iptables
EOF
chmod 440 "$SUDOERS_FILE"
echo "  Configured sudo permissions"

# Configure iptables persistence
echo "  Configuring iptables persistence..."
apt-get install -y iptables-persistent

# Install systemd service
echo -e "\n${GREEN}[7/8] Installing systemd service...${NC}"
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=WiFi Monitor Pi Agent
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=$INSTALL_DIR/venv/bin/python3 run.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=wifi-monitor

# Security hardening
NoNewPrivileges=false
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$INSTALL_DIR/logs

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo "  Installed systemd service"

# Configure log rotation
echo -e "\n${GREEN}[8/8] Configuring log rotation...${NC}"
cat > "/etc/logrotate.d/$SERVICE_NAME" << EOF
$INSTALL_DIR/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 $USER $USER
}
EOF
echo "  Configured log rotation"

# Configuration instructions
echo -e "\n${GREEN}╔════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║      Installation Complete! 🎉         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Configure the agent:"
echo -e "   ${GREEN}nano $INSTALL_DIR/config.yaml${NC}"
echo ""
echo "   Required settings:"
echo "     • api_base_url: Your backend server URL"
echo "     • auth.email: Your admin email"
echo "     • auth.password: Your admin password"
echo "     • interface: Network interface (wlan0 or eth0)"
echo "     • simulation_mode: Set to false for production"
echo ""
echo "2. Test the configuration:"
echo -e "   ${GREEN}sudo -u $USER $INSTALL_DIR/venv/bin/python3 $INSTALL_DIR/run.py --test-config${NC}"
echo ""
echo "3. Start the service:"
echo -e "   ${GREEN}systemctl enable $SERVICE_NAME${NC}"
echo -e "   ${GREEN}systemctl start $SERVICE_NAME${NC}"
echo ""
echo "4. Check service status:"
echo -e "   ${GREEN}systemctl status $SERVICE_NAME${NC}"
echo ""
echo "5. View logs:"
echo -e "   ${GREEN}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "   ${GREEN}tail -f $INSTALL_DIR/logs/*.log${NC}"
echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "  • If scanning fails, ensure arp-scan or nmap is installed"
echo "  • If iptables fails, run with sudo or check permissions"
echo "  • Check logs in $INSTALL_DIR/logs/ for errors"
echo ""
echo -e "${GREEN}Installation location: $INSTALL_DIR${NC}"
echo -e "${GREEN}Service user: $USER${NC}"
echo ""
