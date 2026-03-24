#!/bin/bash
# Quick reference for WiFi Monitor Hotspot Mode
# Display helpful commands

cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║        WiFi Monitor - Hotspot Quick Reference                ║
╚══════════════════════════════════════════════════════════════╝

📋 SETUP COMMANDS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Complete setup (one command!)
sudo bash setup-complete.sh

# Setup hotspot only
sudo bash setup-hotspot.sh

# Test hotspot
sudo bash test-hotspot.sh

# Install monitor agent
sudo bash install.sh


📊 STATUS CHECKS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Overall hotspot status
hotspot-status

# Check all services
systemctl status hostapd dnsmasq wifi-monitor

# WiFi status
iwconfig wlan0

# Interface IPs
ip addr show wlan0
ip addr show eth0


👥 CONNECTED DEVICES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# See all connected devices (ARP table)
cat /proc/net/arp

# See DHCP leases
cat /var/lib/misc/dnsmasq.leases

# Count connected devices
arp -i wlan0 -n | tail -n +2 | wc -l

# Watch DHCP activity
sudo tail -f /var/log/syslog | grep DHCP


📝 LOGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Monitor agent logs (real-time)
sudo journalctl -u wifi-monitor -f

# Hotspot logs
sudo journalctl -u hostapd -f

# DHCP logs  
sudo journalctl -u dnsmasq -f

# All system logs
sudo tail -f /var/log/syslog

# Application logs
tail -f /opt/wifi-monitor/logs/agent_*.log


🔧 SERVICE MANAGEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Restart hotspot
sudo systemctl restart hostapd dnsmasq

# Restart monitoring
sudo systemctl restart wifi-monitor

# Stop hotspot
sudo systemctl stop hostapd dnsmasq

# Start hotspot
sudo systemctl start hostapd dnsmasq

# Enable on boot
sudo systemctl enable hostapd dnsmasq wifi-monitor

# Disable on boot
sudo systemctl disable hostapd dnsmasq wifi-monitor


⚙️  CONFIGURATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Edit hotspot settings (SSID, password, channel)
sudo nano /etc/hostapd/hostapd.conf

# Edit DHCP settings (IP range, DNS)
sudo nano /etc/dnsmasq.conf

# Edit monitor settings
sudo nano /opt/wifi-monitor/config.yaml

# Test monitor config
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 \
    /opt/wifi-monitor/run.py --test-config


🌐 NETWORK TESTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Test internet from Pi
ping -c 3 8.8.8.8

# Check IP forwarding (should be 1)
cat /proc/sys/net/ipv4/ip_forward

# Check NAT rules
sudo iptables -t nat -L -n -v

# Check forwarding rules
sudo iptables -L FORWARD -n -v

# Check monitoring rules
sudo iptables -L WIFI_MONITOR_OUT -n -v
sudo iptables -L WIFI_MONITOR_IN -n -v


🔍 TROUBLESHOOTING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Hotspot not visible?
sudo systemctl status hostapd
sudo journalctl -u hostapd -n 50

# Devices can't get IP?
sudo systemctl status dnsmasq
sudo journalctl -u dnsmasq -n 50

# No internet on devices?
cat /proc/sys/net/ipv4/ip_forward
sudo iptables -t nat -L

# Monitoring not working?
sudo systemctl status wifi-monitor
sudo journalctl -u wifi-monitor -n 50

# Run full diagnostic
sudo bash test-hotspot.sh


📱 CLIENT TESTING (from connected device)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Check IP (should be 192.168.50.x)
ip addr    # Linux
ipconfig   # Windows
ifconfig   # Mac

# Check gateway (should be 192.168.50.1)
ip route   # Linux
route print # Windows
netstat -nr # Mac

# Test internet
ping 8.8.8.8

# Test DNS
nslookup google.com


📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

cat HOTSPOT_SETUP.md          # Complete setup guide
cat NETWORK_ARCHITECTURE.md   # Network diagrams & flows
cat HOTSPOT_MODE_SUMMARY.md   # What was built
cat QUICKREF.md               # Command reference
cat README.md                 # Overview


💾 BACKUP & RESTORE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Backup configs
sudo tar czf wifi-monitor-backup.tar.gz \
    /etc/hostapd/hostapd.conf \
    /etc/dnsmasq.conf \
    /etc/dhcpcd.conf \
    /opt/wifi-monitor/config.yaml

# Save iptables
sudo iptables-save > iptables-backup.rules

# Restore iptables
sudo iptables-restore < iptables-backup.rules


🔐 SECURITY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Change WiFi password
sudo nano /etc/hostapd/hostapd.conf
# Edit: wpa_passphrase=NewPassword123
sudo systemctl restart hostapd

# Change Pi password
passwd

# Update system
sudo apt update && sudo apt upgrade -y

# Check failed login attempts
sudo journalctl -u ssh | grep Failed


📊 USAGE STATISTICS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# View interface stats
cat /proc/net/dev

# View traffic by device (iptables counters)
sudo iptables -L WIFI_MONITOR_OUT -n -v -x
sudo iptables -L WIFI_MONITOR_IN -n -v -x

# System resource usage
top
htop  # if installed


🔄 MAINTENANCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Check disk space
df -h

# Check log sizes
du -sh /var/log
du -sh /opt/wifi-monitor/logs

# Clean old logs
sudo journalctl --vacuum-time=7d
sudo rm /opt/wifi-monitor/logs/*.log.*.gz

# Update Python packages
cd /opt/wifi-monitor
sudo -u wifi-monitor venv/bin/pip install --upgrade -r requirements.txt

# Reboot Pi
sudo reboot


🚀 QUICK ACTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Restart everything
sudo systemctl restart hostapd dnsmasq wifi-monitor

# Check all is working
hotspot-status && sudo systemctl status wifi-monitor

# Watch monitoring live
sudo journalctl -u wifi-monitor -f

# See who's connected
cat /proc/net/arp | grep wlan0

# Full system test
sudo bash test-hotspot.sh


💡 TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Default hotspot: WiFi-Monitor / monitor123
• Default gateway: 192.168.50.1
• DHCP range: 192.168.50.10 - 192.168.50.250
• Config located: /opt/wifi-monitor/config.yaml
• To hide SSID: Edit /etc/hostapd/hostapd.conf
  Set: ignore_broadcast_ssid=1


📱 CONNECT TO HOTSPOT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. On phone/laptop: Scan WiFi networks
2. Find: WiFi-Monitor (or your custom SSID)
3. Password: monitor123 (or your custom password)
4. Should get IP: 192.168.50.x
5. Test internet: Open web browser
6. Check monitoring: View backend dashboard


═══════════════════════════════════════════════════════════════

For detailed help:
  cat HOTSPOT_SETUP.md
  cat NETWORK_ARCHITECTURE.md

Happy monitoring! 🎉

═══════════════════════════════════════════════════════════════
EOF
