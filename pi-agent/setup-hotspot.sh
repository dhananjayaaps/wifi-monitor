#!/bin/bash
# WiFi Monitor - Hotspot Setup Script
# Configures Raspberry Pi as WiFi Access Point with internet sharing
# 
# Network Architecture:
#   Internet -> eth0 (Pi) -> wlan0 (Pi Hotspot) -> Client Devices
#
# This script sets up:
# - hostapd (WiFi Access Point daemon)
# - dnsmasq (DHCP/DNS server)
# - IP forwarding and NAT
# - Network monitoring rules

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
HOTSPOT_SSID="${HOTSPOT_SSID:-WiFi-Monitor}"
HOTSPOT_PASSWORD="${HOTSPOT_PASSWORD:-monitor123}"
HOTSPOT_CHANNEL="${HOTSPOT_CHANNEL:-7}"
WLAN_INTERFACE="${WLAN_INTERFACE:-wlan0}"
INTERNET_INTERFACE="${INTERNET_INTERFACE:-eth0}"
HOTSPOT_IP="192.168.50.1"
DHCP_RANGE_START="192.168.50.10"
DHCP_RANGE_END="192.168.50.250"

echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  WiFi Monitor - Hotspot Setup           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}✗ Please run as root (use sudo)${NC}"
    exit 1
fi

# Display configuration
echo -e "${BLUE}Configuration:${NC}"
echo "  Hotspot SSID: $HOTSPOT_SSID"
echo "  Password: ${HOTSPOT_PASSWORD:0:3}***"
echo "  Channel: $HOTSPOT_CHANNEL"
echo "  WiFi Interface: $WLAN_INTERFACE"
echo "  Internet Interface: $INTERNET_INTERFACE"
echo "  Hotspot IP: $HOTSPOT_IP"
echo "  DHCP Range: $DHCP_RANGE_START - $DHCP_RANGE_END"
echo ""
read -p "Continue with these settings? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Setup cancelled. Edit script variables to change settings."
    exit 0
fi

# Install required packages
echo -e "\n${GREEN}[1/8] Installing required packages...${NC}"
apt-get update -qq
apt-get install -y \
    hostapd \
    dnsmasq \
    iptables \
    iptables-persistent \
    net-tools \
    wireless-tools \
    rfkill

# Stop services for configuration
echo -e "\n${GREEN}[2/8] Stopping services...${NC}"
systemctl stop hostapd 2>/dev/null || true
systemctl stop dnsmasq 2>/dev/null || true

# Backup existing configurations
echo -e "\n${GREEN}[3/8] Backing up existing configurations...${NC}"
[ -f /etc/hostapd/hostapd.conf ] && cp /etc/hostapd/hostapd.conf /etc/hostapd/hostapd.conf.backup
[ -f /etc/dnsmasq.conf ] && cp /etc/dnsmasq.conf /etc/dnsmasq.conf.backup
[ -f /etc/dhcpcd.conf ] && cp /etc/dhcpcd.conf /etc/dhcpcd.conf.backup

# Configure static IP for wlan0
echo -e "\n${GREEN}[4/8] Configuring static IP for hotspot interface...${NC}"
cat >> /etc/dhcpcd.conf << EOF

# WiFi Monitor Hotspot Configuration
interface $WLAN_INTERFACE
    static ip_address=$HOTSPOT_IP/24
    nohook wpa_supplicant
EOF
echo "  Configured $WLAN_INTERFACE with IP $HOTSPOT_IP"

# Configure hostapd
echo -e "\n${GREEN}[5/8] Configuring hostapd (WiFi Access Point)...${NC}"
cat > /etc/hostapd/hostapd.conf << EOF
# WiFi Monitor Hotspot Configuration
interface=$WLAN_INTERFACE
driver=nl80211
ssid=$HOTSPOT_SSID
hw_mode=g
channel=$HOTSPOT_CHANNEL
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=$HOTSPOT_PASSWORD
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# Logging
logger_syslog=-1
logger_syslog_level=2
logger_stdout=-1
logger_stdout_level=2

# Performance tuning
beacon_int=100
dtim_period=2
max_num_sta=20
rts_threshold=2347
fragm_threshold=2346
EOF

# Set hostapd configuration path
sed -i 's|#DAEMON_CONF=""|DAEMON_CONF="/etc/hostapd/hostapd.conf"|g' /etc/default/hostapd
echo "  Created hostapd configuration"

# Configure dnsmasq
echo -e "\n${GREEN}[6/8] Configuring dnsmasq (DHCP + DNS)...${NC}"
mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
cat > /etc/dnsmasq.conf << EOF
# WiFi Monitor Hotspot - DNS/DHCP Configuration

# Interface to listen on
interface=$WLAN_INTERFACE

# Bind to interface
bind-interfaces

# DHCP range
dhcp-range=$DHCP_RANGE_START,$DHCP_RANGE_END,255.255.255.0,24h

# DNS
# Use your internet interface's DNS or specify custom
server=8.8.8.8
server=8.8.4.4

# Local domain
domain=wifimonitor.local
local=/wifimonitor.local/

# DHCP options
dhcp-option=3,$HOTSPOT_IP    # Gateway
dhcp-option=6,$HOTSPOT_IP    # DNS server

# Logging
log-queries
log-dhcp

# Other settings
bogus-priv
domain-needed
expand-hosts
EOF
echo "  Created dnsmasq configuration"

# Enable IP forwarding
echo -e "\n${GREEN}[7/8] Enabling IP forwarding and NAT...${NC}"
# Uncomment or add ip_forward
if grep -q "^#net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    sed -i 's/^#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/' /etc/sysctl.conf
elif ! grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
fi

# Enable IP forwarding now
echo 1 > /proc/sys/net/ipv4/ip_forward
echo "  IP forwarding enabled"

# Configure NAT with iptables
echo -e "\n${GREEN}[8/8] Configuring NAT (Network Address Translation)...${NC}"

# Flush existing rules
iptables -F
iptables -t nat -F
iptables -t mangle -F
iptables -X

# Set default policies
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT

# NAT configuration
iptables -t nat -A POSTROUTING -o $INTERNET_INTERFACE -j MASQUERADE

# Forward traffic between interfaces
iptables -A FORWARD -i $INTERNET_INTERFACE -o $WLAN_INTERFACE -m state --state RELATED,ESTABLISHED -j ACCEPT
iptables -A FORWARD -i $WLAN_INTERFACE -o $INTERNET_INTERFACE -j ACCEPT

# Allow traffic on loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Allow DHCP and DNS on hotspot interface
iptables -A INPUT -i $WLAN_INTERFACE -p udp --dport 67 -j ACCEPT  # DHCP
iptables -A INPUT -i $WLAN_INTERFACE -p udp --dport 53 -j ACCEPT  # DNS
iptables -A INPUT -i $WLAN_INTERFACE -p tcp --dport 53 -j ACCEPT  # DNS

# Save iptables rules
netfilter-persistent save
echo "  NAT and forwarding rules configured"

# Unmask and enable services
echo -e "\n${GREEN}Enabling hotspot services...${NC}"
systemctl unmask hostapd
systemctl enable hostapd
systemctl enable dnsmasq

# Restart networking
echo -e "\n${GREEN}Restarting network services...${NC}"
systemctl restart dhcpcd
sleep 2

# Start services
echo -e "\n${GREEN}Starting hotspot services...${NC}"
systemctl start hostapd
systemctl start dnsmasq

# Check status
echo -e "\n${GREEN}Checking service status...${NC}"
sleep 2

HOSTAPD_STATUS=$(systemctl is-active hostapd)
DNSMASQ_STATUS=$(systemctl is-active dnsmasq)

if [ "$HOSTAPD_STATUS" = "active" ]; then
    echo -e "  ${GREEN}✓ hostapd: running${NC}"
else
    echo -e "  ${RED}✗ hostapd: $HOSTAPD_STATUS${NC}"
    echo -e "  ${YELLOW}Check logs: journalctl -u hostapd -n 50${NC}"
fi

if [ "$DNSMASQ_STATUS" = "active" ]; then
    echo -e "  ${GREEN}✓ dnsmasq: running${NC}"
else
    echo -e "  ${RED}✗ dnsmasq: $DNSMASQ_STATUS${NC}"
    echo -e "  ${YELLOW}Check logs: journalctl -u dnsmasq -n 50${NC}"
fi

# Display interface status
echo -e "\n${GREEN}Interface status:${NC}"
ip addr show $WLAN_INTERFACE | grep "inet " || echo "  No IP assigned yet"
echo ""
iwconfig $WLAN_INTERFACE 2>/dev/null | grep -E "ESSID|Mode" || echo "  Interface not configured"

# Success message
echo -e "\n${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     Hotspot Setup Complete! 🎉           ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}Your WiFi Hotspot Details:${NC}"
echo "  📡 SSID: $HOTSPOT_SSID"
echo "  🔑 Password: $HOTSPOT_PASSWORD"
echo "  📶 Channel: $HOTSPOT_CHANNEL"
echo "  🌐 Gateway IP: $HOTSPOT_IP"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Connect a device to the '$HOTSPOT_SSID' WiFi network"
echo "2. Test internet connectivity on the connected device"
echo "3. Run test script: ${GREEN}bash test-hotspot.sh${NC}"
echo "4. Configure WiFi Monitor agent: ${GREEN}nano /opt/wifi-monitor/config.yaml${NC}"
echo "   - Set: interface: \"$WLAN_INTERFACE\""
echo "   - Set: simulation_mode: false"
echo "5. Start monitoring: ${GREEN}systemctl start wifi-monitor${NC}"
echo ""
echo -e "${YELLOW}Troubleshooting:${NC}"
echo "  View hostapd logs: ${GREEN}journalctl -u hostapd -f${NC}"
echo "  View dnsmasq logs: ${GREEN}journalctl -u dnsmasq -f${NC}"
echo "  Test connectivity: ${GREEN}bash test-hotspot.sh${NC}"
echo "  Check WiFi status: ${GREEN}iwconfig $WLAN_INTERFACE${NC}"
echo "  View connected devices: ${GREEN}cat /proc/net/arp${NC}"
echo ""
echo -e "${BLUE}To make changes:${NC}"
echo "  Edit hostapd config: ${GREEN}nano /etc/hostapd/hostapd.conf${NC}"
echo "  Edit dnsmasq config: ${GREEN}nano /etc/dnsmasq.conf${NC}"
echo "  Then restart: ${GREEN}systemctl restart hostapd dnsmasq${NC}"
echo ""

# Create status check script
cat > /usr/local/bin/hotspot-status << 'STATUSEOF'
#!/bin/bash
echo "=== WiFi Monitor Hotspot Status ==="
echo ""
echo "Services:"
systemctl is-active hostapd && echo "  ✓ hostapd: running" || echo "  ✗ hostapd: stopped"
systemctl is-active dnsmasq && echo "  ✓ dnsmasq: running" || echo "  ✗ dnsmasq: stopped"
echo ""
echo "WiFi Interface:"
iwconfig wlan0 2>/dev/null | grep -E "ESSID|Mode|Frequency" || echo "  Not configured"
echo ""
echo "IP Configuration:"
ip addr show wlan0 | grep "inet " || echo "  No IP"
echo ""
echo "Connected Devices:"
arp -i wlan0 -n | tail -n +2 | wc -l | xargs echo "  Total:"
echo ""
echo "Recent DHCP Leases:"
grep DHCP /var/log/syslog | tail -5
STATUSEOF
chmod +x /usr/local/bin/hotspot-status

echo -e "${GREEN}Created status check script: ${BLUE}hotspot-status${NC}"
echo ""
