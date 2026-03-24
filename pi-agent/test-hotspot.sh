#!/bin/bash
# WiFi Monitor - Hotspot Test Script
# Tests all aspects of the WiFi hotspot configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
WLAN_INTERFACE="${WLAN_INTERFACE:-wlan0}"
INTERNET_INTERFACE="${INTERNET_INTERFACE:-eth0}"
HOTSPOT_IP="192.168.50.1"

echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  WiFi Monitor - Hotspot Test            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""

PASS=0
FAIL=0
WARN=0

print_test() {
    local name="$1"
    local status="$2"
    local details="$3"
    
    if [ "$status" = "pass" ]; then
        echo -e "${GREEN}✓${NC} $name"
        ((PASS++))
    elif [ "$status" = "fail" ]; then
        echo -e "${RED}✗${NC} $name"
        ((FAIL++))
    else
        echo -e "${YELLOW}⚠${NC} $name"
        ((WARN++))
    fi
    
    if [ -n "$details" ]; then
        echo -e "  ${details}"
    fi
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}Note: Some tests require root access. Run with sudo for complete testing.${NC}"
    echo ""
fi

# Test 1: Interface existence
echo -e "${BLUE}[1/12] Checking network interfaces...${NC}"
if ip link show $WLAN_INTERFACE &>/dev/null; then
    print_test "WiFi interface ($WLAN_INTERFACE) exists" "pass"
else
    print_test "WiFi interface ($WLAN_INTERFACE) exists" "fail" "Interface not found"
fi

if ip link show $INTERNET_INTERFACE &>/dev/null; then
    print_test "Internet interface ($INTERNET_INTERFACE) exists" "pass"
else
    print_test "Internet interface ($INTERNET_INTERFACE) exists" "warn" "Interface not found - check if connected"
fi
echo ""

# Test 2: Interface status
echo -e "${BLUE}[2/12] Checking interface status...${NC}"
WLAN_UP=$(ip link show $WLAN_INTERFACE 2>/dev/null | grep -c "state UP" || echo "0")
if [ "$WLAN_UP" -eq 1 ]; then
    print_test "WiFi interface is UP" "pass"
else
    print_test "WiFi interface is UP" "fail" "Interface is DOWN"
fi

INET_UP=$(ip link show $INTERNET_INTERFACE 2>/dev/null | grep -c "state UP" || echo "0")
if [ "$INET_UP" -eq 1 ]; then
    print_test "Internet interface is UP" "pass"
else
    print_test "Internet interface is UP" "warn" "Interface is DOWN - no internet source"
fi
echo ""

# Test 3: IP configuration
echo -e "${BLUE}[3/12] Checking IP configuration...${NC}"
WLAN_IP=$(ip addr show $WLAN_INTERFACE 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1)
if [ -n "$WLAN_IP" ]; then
    print_test "WiFi interface has IP" "pass" "IP: $WLAN_IP"
    if [ "$WLAN_IP" = "$HOTSPOT_IP" ]; then
        print_test "Correct hotspot IP configured" "pass"
    else
        print_test "Correct hotspot IP configured" "warn" "Expected $HOTSPOT_IP, got $WLAN_IP"
    fi
else
    print_test "WiFi interface has IP" "fail" "No IP assigned"
fi

INET_IP=$(ip addr show $INTERNET_INTERFACE 2>/dev/null | grep "inet " | awk '{print $2}' | cut -d'/' -f1 || echo "")
if [ -n "$INET_IP" ]; then
    print_test "Internet interface has IP" "pass" "IP: $INET_IP"
else
    print_test "Internet interface has IP" "warn" "No IP - cannot provide internet"
fi
echo ""

# Test 4: hostapd service
echo -e "${BLUE}[4/12] Checking hostapd (WiFi AP)...${NC}"
if systemctl is-active --quiet hostapd; then
    print_test "hostapd service is running" "pass"
else
    print_test "hostapd service is running" "fail" "Service not active"
fi

if systemctl is-enabled --quiet hostapd; then
    print_test "hostapd enabled on boot" "pass"
else
    print_test "hostapd enabled on boot" "warn" "Service not enabled"
fi

if [ -f /etc/hostapd/hostapd.conf ]; then
    print_test "hostapd config exists" "pass"
    SSID=$(grep "^ssid=" /etc/hostapd/hostapd.conf | cut -d'=' -f2)
    if [ -n "$SSID" ]; then
        print_test "SSID configured" "pass" "SSID: $SSID"
    fi
else
    print_test "hostapd config exists" "fail" "/etc/hostapd/hostapd.conf not found"
fi
echo ""

# Test 5: dnsmasq service
echo -e "${BLUE}[5/12] Checking dnsmasq (DHCP/DNS)...${NC}"
if systemctl is-active --quiet dnsmasq; then
    print_test "dnsmasq service is running" "pass"
else
    print_test "dnsmasq service is running" "fail" "Service not active"
fi

if systemctl is-enabled --quiet dnsmasq; then
    print_test "dnsmasq enabled on boot" "pass"
else
    print_test "dnsmasq enabled on boot" "warn" "Service not enabled"
fi

if [ -f /etc/dnsmasq.conf ]; then
    print_test "dnsmasq config exists" "pass"
else
    print_test "dnsmasq config exists" "fail" "/etc/dnsmasq.conf not found"
fi
echo ""

# Test 6: IP forwarding
echo -e "${BLUE}[6/12] Checking IP forwarding...${NC}"
IP_FORWARD=$(cat /proc/sys/net/ipv4/ip_forward)
if [ "$IP_FORWARD" = "1" ]; then
    print_test "IP forwarding enabled" "pass"
else
    print_test "IP forwarding enabled" "fail" "IP forwarding is disabled"
fi

if grep -q "^net.ipv4.ip_forward=1" /etc/sysctl.conf; then
    print_test "IP forwarding persistent" "pass"
else
    print_test "IP forwarding persistent" "warn" "Not configured in /etc/sysctl.conf"
fi
echo ""

# Test 7: NAT rules
echo -e "${BLUE}[7/12] Checking NAT (iptables)...${NC}"
NAT_COUNT=$(iptables -t nat -L POSTROUTING -n 2>/dev/null | grep -c MASQUERADE || echo "0")
if [ "$NAT_COUNT" -gt 0 ]; then
    print_test "NAT (MASQUERADE) configured" "pass" "Found $NAT_COUNT rule(s)"
else
    print_test "NAT (MASQUERADE) configured" "fail" "No MASQUERADE rules found"
fi

FORWARD_COUNT=$(iptables -L FORWARD -n 2>/dev/null | grep -c ACCEPT || echo "0")
if [ "$FORWARD_COUNT" -gt 0 ]; then
    print_test "Forwarding rules configured" "pass" "Found $FORWARD_COUNT rule(s)"
else
    print_test "Forwarding rules configured" "warn" "Limited forwarding rules"
fi
echo ""

# Test 8: WiFi radio
echo -e "${BLUE}[8/12] Checking WiFi radio...${NC}"
if command -v iwconfig &>/dev/null; then
    ESSID=$(iwconfig $WLAN_INTERFACE 2>/dev/null | grep "ESSID" | cut -d':' -f2 | tr -d '"' || echo "")
    if [ -n "$ESSID" ]; then
        print_test "WiFi hotspot is broadcasting" "pass" "ESSID: $ESSID"
    else
        print_test "WiFi hotspot is broadcasting" "fail" "No ESSID detected"
    fi
    
    MODE=$(iwconfig $WLAN_INTERFACE 2>/dev/null | grep "Mode:" | awk '{print $1}' | cut -d':' -f2 || echo "")
    if [ "$MODE" = "Master" ] || [ "$MODE" = "AP" ]; then
        print_test "WiFi in AP mode" "pass" "Mode: $MODE"
    else
        print_test "WiFi in AP mode" "warn" "Mode: $MODE (expected Master/AP)"
    fi
else
    print_test "WiFi radio check" "warn" "iwconfig not available"
fi
echo ""

# Test 9: DHCP leases
echo -e "${BLUE}[9/12] Checking DHCP leases...${NC}"
if [ -f /var/lib/misc/dnsmasq.leases ]; then
    LEASE_COUNT=$(wc -l < /var/lib/misc/dnsmasq.leases)
    if [ "$LEASE_COUNT" -gt 0 ]; then
        print_test "DHCP leases active" "pass" "$LEASE_COUNT device(s) with leases"
        echo "  Current leases:"
        cat /var/lib/misc/dnsmasq.leases | while read line; do
            IP=$(echo $line | awk '{print $3}')
            MAC=$(echo $line | awk '{print $2}')
            NAME=$(echo $line | awk '{print $4}')
            echo "    - $IP ($MAC) ${NAME:+- $NAME}"
        done
    else
        print_test "DHCP leases active" "warn" "No active leases (no devices connected)"
    fi
else
    print_test "DHCP leases file" "warn" "Leases file not found"
fi
echo ""

# Test 10: Connected devices (ARP table)
echo -e "${BLUE}[10/12] Checking connected devices (ARP)...${NC}"
ARP_COUNT=$(arp -i $WLAN_INTERFACE -n 2>/dev/null | tail -n +2 | grep -v "incomplete" | wc -l || echo "0")
if [ "$ARP_COUNT" -gt 0 ]; then
    print_test "Devices in ARP table" "pass" "$ARP_COUNT device(s) visible"
    echo "  Connected devices:"
    arp -i $WLAN_INTERFACE -n 2>/dev/null | tail -n +2 | grep -v "incomplete" | while read line; do
        IP=$(echo $line | awk '{print $1}')
        MAC=$(echo $line | awk '{print $3}')
        echo "    - $IP ($MAC)"
    done
else
    print_test "Devices in ARP table" "warn" "No devices in ARP table"
fi
echo ""

# Test 11: Internet connectivity
echo -e "${BLUE}[11/12] Checking internet connectivity...${NC}"
if ping -c 1 -W 2 8.8.8.8 &>/dev/null; then
    print_test "Pi can reach internet" "pass" "Ping to 8.8.8.8 successful"
else
    print_test "Pi can reach internet" "fail" "Cannot ping 8.8.8.8"
fi

if [ -n "$INET_IP" ]; then
    GATEWAY=$(ip route | grep default | grep $INTERNET_INTERFACE | awk '{print $3}')
    if [ -n "$GATEWAY" ]; then
        print_test "Default gateway configured" "pass" "Gateway: $GATEWAY"
        if ping -c 1 -W 2 $GATEWAY &>/dev/null; then
            print_test "Can reach gateway" "pass"
        else
            print_test "Can reach gateway" "warn" "Gateway unreachable"
        fi
    else
        print_test "Default gateway configured" "warn" "No default gateway"
    fi
fi
echo ""

# Test 12: DNS resolution
echo -e "${BLUE}[12/12] Checking DNS resolution...${NC}"
if nslookup google.com &>/dev/null; then
    print_test "DNS resolution works" "pass"
else
    print_test "DNS resolution works" "warn" "DNS lookup failed"
fi
echo ""

# Summary
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║          Test Summary                    ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✓ Passed:${NC}  $PASS"
echo -e "  ${YELLOW}⚠ Warnings:${NC} $WARN"
echo -e "  ${RED}✗ Failed:${NC}  $FAIL"
echo ""

if [ $FAIL -eq 0 ]; then
    if [ $WARN -eq 0 ]; then
        echo -e "${GREEN}═══════════════════════════════════════════${NC}"
        echo -e "${GREEN}   All tests passed! Hotspot is ready! 🎉${NC}"
        echo -e "${GREEN}═══════════════════════════════════════════${NC}"
        echo ""
        echo -e "${BLUE}Next steps:${NC}"
        echo "1. Connect a device to your WiFi hotspot"
        echo "2. Test internet on the device"
        echo "3. Start WiFi Monitor: ${GREEN}systemctl start wifi-monitor${NC}"
        echo "4. View monitoring: ${GREEN}journalctl -u wifi-monitor -f${NC}"
    else
        echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
        echo -e "${YELLOW}  Tests passed with warnings.${NC}"
        echo -e "${YELLOW}═══════════════════════════════════════════${NC}"
        echo ""
        echo "The hotspot should work, but review warnings above."
        echo "Most warnings are okay if no devices are connected yet."
    fi
else
    echo -e "${RED}═══════════════════════════════════════════${NC}"
    echo -e "${RED}   Some tests failed. Review issues above.${NC}"
    echo -e "${RED}═══════════════════════════════════════════${NC}"
    echo ""
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "  View logs:"
    echo "    ${GREEN}journalctl -u hostapd -n 50${NC}"
    echo "    ${GREEN}journalctl -u dnsmasq -n 50${NC}"
    echo "    ${GREEN}tail -f /var/log/syslog${NC}"
    echo ""
    echo "  Check configuration:"
    echo "    ${GREEN}cat /etc/hostapd/hostapd.conf${NC}"
    echo "    ${GREEN}cat /etc/dnsmasq.conf${NC}"
    echo "    ${GREEN}cat /etc/dhcpcd.conf${NC}"
    echo ""
    echo "  Restart services:"
    echo "    ${GREEN}systemctl restart hostapd dnsmasq${NC}"
    echo ""
    echo "  Re-run setup:"
    echo "    ${GREEN}bash setup-hotspot.sh${NC}"
fi
echo ""

# Exit with appropriate code
if [ $FAIL -gt 0 ]; then
    exit 1
elif [ $WARN -gt 0 ]; then
    exit 0
else
    exit 0
fi
