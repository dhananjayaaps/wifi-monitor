# WiFi Monitor - Hotspot Mode Setup Guide

## 📡 Overview

This guide shows you how to set up your Raspberry Pi as a **WiFi Hotspot (Access Point)** that:
1. Gets internet from Ethernet or USB dongle
2. Broadcasts its own WiFi network
3. Shares internet with connected devices
4. Monitors all device traffic and usage

## 🎯 What You'll Build

```
Internet → Raspberry Pi (eth0/usb0) → WiFi Hotspot (wlan0) → Your Devices
           └─ Monitors all connected devices and their traffic
```

## 📋 Prerequisites

### Hardware
- Raspberry Pi 3B+ or newer (Pi 4 recommended)
- MicroSD card (16GB+)
- Power supply
- **Internet source** (choose one):
  - ✅ Ethernet cable connected to router
  - ✅ USB 4G/LTE dongle

### Software
- Raspberry Pi OS (Lite or Desktop)
- SSH access to your Pi

### Backend
- WiFi Monitor backend server running and accessible
- Admin credentials for authentication

## 🚀 Quick Start (5 Minutes)

### All-in-One Setup

Run this single command to set up everything:

```bash
cd ~/wifi-monitor/pi-agent
sudo bash setup-complete.sh
```

This wizard will:
1. Ask for your hotspot settings (SSID, password, etc.)
2. Ask for backend server details
3. Set up the WiFi hotspot
4. Install the monitoring agent
5. Configure everything
6. Start all services

**That's it!** Follow the prompts and you're done.

---

## 📝 Manual Setup (Step-by-Step)

If you prefer manual control or the wizard fails:

### Step 1: Prepare Your Pi

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Reboot
sudo reboot
```

### Step 2: Connect Internet Source

**Option A: Ethernet**
- Plug Ethernet cable from your router into Pi's eth0 port
- Verify connection: `ping google.com`

**Option B: USB Dongle**
- Insert USB 4G/LTE dongle
- Install dongle drivers (varies by manufacturer)
- Verify connection: `ping google.com`
- Note the interface name: `ip link` (usually `usb0` or `wwan0`)

### Step 3: Download WiFi Monitor

```bash
cd ~
git clone <your-repo-url> wifi-monitor
cd wifi-monitor/pi-agent
```

### Step 4: Set Up WiFi Hotspot

```bash
# Run hotspot setup script
sudo bash setup-hotspot.sh
```

**What it does:**
- Installs `hostapd` (WiFi access point software)
- Installs `dnsmasq` (DHCP + DNS server)
- Configures static IP for wlan0 (192.168.50.1)
- Sets up NAT (Network Address Translation)
- Enables IP forwarding
- Creates iptables rules

**Default settings:**
- SSID: `WiFi-Monitor`
- Password: `monitor123`
- IP Range: `192.168.50.10` - `192.168.50.250`
- Gateway: `192.168.50.1`

### Step 5: Test Hotspot

```bash
# Run comprehensive tests
sudo bash test-hotspot.sh
```

This tests:
- ✓ Services are running
- ✓ WiFi is broadcasting
- ✓ DHCP is working
- ✓ NAT is configured
- ✓ Internet is accessible

**If tests pass:** Continue to next step  
**If tests fail:** Check logs and troubleshoot (see below)

### Step 6: Connect a Test Device

1. On your phone/laptop, scan for WiFi networks
2. Find `WiFi-Monitor` (or your custom SSID)
3. Connect with password `monitor123`
4. Test internet access (open a website)

**What should happen:**
- Device gets IP: `192.168.50.x`
- Device has internet access
- Device appears in Pi's ARP table

**Verify:**
```bash
# See connected devices
cat /proc/net/arp

# See DHCP leases
cat /var/lib/misc/dnsmasq.leases
```

### Step 7: Install Monitor Agent

```bash
# Run agent installation
sudo bash install.sh
```

This installs the WiFi monitoring agent that tracks devices and traffic.

### Step 8: Configure Agent

```bash
# Edit configuration
sudo nano /opt/wifi-monitor/config.yaml
```

**Required settings:**
```yaml
# Backend server URL (CHANGE THIS!)
api_base_url: "http://192.168.1.100:5000/api/v1"

# Network interface (hotspot interface)
interface: "wlan0"

# Enable hotspot mode
hotspot_mode: true

# Internet interface (where internet comes from)
internet_interface: "eth0"  # or "usb0" for dongle

# Authentication (CHANGE THIS!)
auth:
  email: "admin@wifi.com"
  password: "admin123"

# Production mode (NOT simulation)
simulation_mode: false

# Intervals
scan_interval: 30
stats_interval: 60

# Logging
log_level: "INFO"
```

Save and exit (Ctrl+X, Y, Enter)

### Step 9: Test Configuration

```bash
# Validate config and test backend connection
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config
```

**Should show:**
- ✓ Configuration loaded successfully
- ✓ Connected to backend
- ✓ Authenticated successfully
- ✓ Agent ready

### Step 10: Start Monitoring

```bash
# Enable service on boot
sudo systemctl enable wifi-monitor

# Start service
sudo systemctl start wifi-monitor

# Check status
sudo systemctl status wifi-monitor
```

**Should show:**
```
● wifi-monitor.service - WiFi Monitor Pi Agent
   Active: active (running)
```

### Step 11: Verify Monitoring

```bash
# Watch logs in real-time
sudo journalctl -u wifi-monitor -f
```

**Should see:**
```
Agent Starting...
✓ Connected to backend
✓ Authenticated successfully
✓ Agent ready
Scanning network...
Found 1 device(s)
✓ Synced 1 devices
Collecting stats...
✓ Ingested 1 stats
```

### Step 12: Check Backend

Open your backend dashboard in a web browser. You should see:
- ✓ Connected devices listed
- ✓ Device details (MAC, IP, manufacturer)
- ✓ Traffic usage (upload/download)
- ✓ Real-time updates

---

## ⚙️ Configuration

### Customize Hotspot Settings

Edit hotspot configuration:
```bash
sudo nano /etc/hostapd/hostapd.conf
```

**Common changes:**
```conf
# Change SSID
ssid=MyCustomNetwork

# Change password (min 8 chars)
wpa_passphrase=MySecurePassword123

# Change channel (1-13)
channel=11

# Hide SSID (0=visible, 1=hidden)
ignore_broadcast_ssid=0

# Max connected devices
max_num_sta=20
```

After changes:
```bash
sudo systemctl restart hostapd
```

### Customize DHCP Settings

Edit DHCP configuration:
```bash
sudo nano /etc/dnsmasq.conf
```

**Common changes:**
```conf
# Change IP range
dhcp-range=192.168.50.10,192.168.50.100,255.255.255.0,24h

# Change lease time (e.g., 12h, 1d)
dhcp-range=...,12h

# Reserve IP for specific device
dhcp-host=aa:bb:cc:dd:ee:ff,192.168.50.50,my-device

# Custom DNS servers
server=1.1.1.1
server=1.0.0.1
```

After changes:
```bash
sudo systemctl restart dnsmasq
```

### Customize Monitoring

Edit monitoring configuration:
```bash
sudo nano /opt/wifi-monitor/config.yaml
```

**Common changes:**
```yaml
# Scan more/less frequently
scan_interval: 60  # seconds

# Collect stats more/less frequently
stats_interval: 120  # seconds

# Enable debug logging
log_level: "DEBUG"
```

After changes:
```bash
sudo systemctl restart wifi-monitor
```

---

## 🔍 Monitoring & Status

### Check Hotspot Status

```bash
# Quick status
hotspot-status

# Detailed checks
sudo systemctl status hostapd    # WiFi AP
sudo systemctl status dnsmasq    # DHCP
iwconfig wlan0                   # WiFi info
ip addr show wlan0               # IP configuration
```

### Check Monitoring Status

```bash
# Service status
sudo systemctl status wifi-monitor

# Live logs
sudo journalctl -u wifi-monitor -f

# Recent logs
sudo journalctl -u wifi-monitor -n 100

# Application logs
tail -f /opt/wifi-monitor/logs/agent_*.log
```

### See Connected Devices

```bash
# ARP table (connected devices)
cat /proc/net/arp

# DHCP leases
cat /var/lib/misc/dnsmasq.leases

# Real-time DHCP activity
sudo tail -f /var/log/syslog | grep DHCP

# Traffic counters
sudo iptables -L WIFI_MONITOR_OUT -n -v
```

---

## 🐛 Troubleshooting

### Hotspot Not Visible

**Check service:**
```bash
sudo systemctl status hostapd
```

**If failed:**
```bash
# View error logs
sudo journalctl -u hostapd -n 50

# Check config syntax
sudo hostapd -d /etc/hostapd/hostapd.conf
```

**Common causes:**
- Wrong channel (try different 1-11)
- WiFi interface busy (kill wpa_supplicant)
- Hardware doesn't support AP mode

**Fix:**
```bash
# Kill interfering processes
sudo killall wpa_supplicant

# Restart service
sudo systemctl restart hostapd
```

### Devices Can't Connect

**Check DHCP:**
```bash
sudo systemctl status dnsmasq
```

**View DHCP activity:**
```bash
sudo tail -f /var/log/syslog | grep DHCP
```

**Common causes:**
- DHCP range exhausted
- dnsmasq not listening on wlan0
- IP conflicts

**Fix:**
```bash
# Restart DHCP
sudo systemctl restart dnsmasq

# Expand DHCP range
sudo nano /etc/dnsmasq.conf
# Change dhcp-range line, then restart
```

### No Internet on Devices

**Check IP forwarding:**
```bash
cat /proc/sys/net/ipv4/ip_forward
# Should show: 1
```

**If 0:**
```bash
sudo echo 1 > /proc/sys/net/ipv4/ip_forward
sudo nano /etc/sysctl.conf
# Add: net.ipv4.ip_forward=1
```

**Check NAT:**
```bash
sudo iptables -t nat -L
# Should show MASQUERADE rule
```

**If missing:**
```bash
# Re-run setup
sudo bash setup-hotspot.sh
```

**Check internet source:**
```bash
# Ping from Pi
ping 8.8.8.8

# Check interface is up
ip addr show eth0  # or usb0
```

### Devices Not Monitored

**Check service:**
```bash
sudo systemctl status wifi-monitor
```

**View errors:**
```bash
sudo journalctl -u wifi-monitor -n 50
```

**Common causes:**
- Wrong interface in config
- Cannot reach backend
- Authentication failed
- Simulation mode still enabled

**Fix:**
```bash
# Check config
sudo nano /opt/wifi-monitor/config.yaml
# Verify:
#   interface: "wlan0"
#   simulation_mode: false
#   api_base_url: correct
#   auth: correct

# Test config
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config

# Restart
sudo systemctl restart wifi-monitor
```

### High CPU Usage

**Check processes:**
```bash
top
# Look for hostapd, dnsmasq, python3
```

**If high:**
- Reduce scan intervals in config
- Check for loops in logs
- Update software
```bash
sudo systemctl restart wifi-monitor
```

### Logs Fill Disk

**Check disk usage:**
```bash
df -h
du -sh /opt/wifi-monitor/logs
du -sh /var/log
```

**Clean logs:**
```bash
# Force log rotation
sudo logrotate -f /etc/logrotate.d/wifi-monitor

# Clear old logs
sudo rm /opt/wifi-monitor/logs/*.log.*.gz
sudo journalctl --vacuum-time=7d
```

---

## 🔧 Advanced Configuration

### Change Hotspot IP Range

**Edit network settings:**
```bash
sudo nano /etc/dhcpcd.conf
```

Find and change:
```conf
interface wlan0
    static ip_address=192.168.100.1/24  # New gateway IP
```

**Edit DHCP range:**
```bash
sudo nano /etc/dnsmasq.conf
```

Change:
```conf
dhcp-range=192.168.100.10,192.168.100.250,255.255.255.0,24h
dhcp-option=3,192.168.100.1   # Gateway
dhcp-option=6,192.168.100.1   # DNS
```

**Restart:**
```bash
sudo systemctl restart dhcpcd
sudo systemctl restart dnsmasq
```

### Use Multiple DNS Servers

```bash
sudo nano /etc/dnsmasq.conf
```

Add:
```conf
server=8.8.8.8       # Google
server=8.8.4.4       # Google
server=1.1.1.1       # Cloudflare
server=1.0.0.1       # Cloudflare
```

### Block Specific Devices

**By MAC address:**
```bash
sudo nano /etc/hostapd/hostapd.conf
```

Add:
```conf
macaddr_acl=0
deny_mac_file=/etc/hostapd/deny.mac
```

Create deny list:
```bash
sudo nano /etc/hostapd/deny.mac
```

Add MAC addresses (one per line):
```
aa:bb:cc:dd:ee:ff
11:22:33:44:55:66
```

Restart:
```bash
sudo systemctl restart hostapd
```

### Traffic Limits Per Device

Use iptables rate limiting (example):
```bash
# Limit device to 1 Mbps
sudo iptables -A FORWARD -m mac --mac-source aa:bb:cc:dd:ee:ff -m limit --limit 1000/s -j ACCEPT
sudo iptables -A FORWARD -m mac --mac-source aa:bb:cc:dd:ee:ff -j DROP
```

---

## 📊 Performance Tuning

### For Many Devices (20+)

```bash
# Increase DHCP range
sudo nano /etc/dnsmasq.conf
dhcp-range=192.168.50.10,192.168.50.250,255.255.255.0,24h

# Increase hostapd limits
sudo nano /etc/hostapd/hostapd.conf
max_num_sta=50

# Reduce monitoring intervals
sudo nano /opt/wifi-monitor/config.yaml
scan_interval: 60
stats_interval: 120
```

### For Low Power / Old Pis

```bash
# Reduce monitoring frequency
scan_interval: 120
stats_interval: 300

# Reduce log level
log_level: "WARNING"
```

---

## 🔐 Security Recommendations

1. **Change default password** (min 12 chars)
2. **Use WPA3** if supported (edit hostapd.conf)
3. **Hide SSID** for private use
4. **Enable MAC filtering** for known devices only
5. **Regular updates:** `sudo apt update && sudo apt upgrade`
6. **Monitor logs** for unusual activity
7. **Use firewall** rules to restrict access
8. **Change Pi password:** `passwd`
9. **Disable SSH** if not needed, or use key-based auth
10. **Keep backend secure** with strong passwords

---

## 📖 Additional Resources

- **Network Architecture:** `NETWORK_ARCHITECTURE.md`
- **Quick Reference:** `QUICKREF.md`
- **Full Setup Guide:** `SETUP_GUIDE.md`
- **Troubleshooting:** See above sections

---

## ✅ Success Checklist

- [ ] Pi has internet (via eth0 or usb0)
- [ ] Hotspot is broadcasting (check on phone)
- [ ] Can connect to hotspot with password
- [ ] Connected device has internet
- [ ] Device appears in ARP table
- [ ] Monitor agent is running
- [ ] Device shows in backend dashboard
- [ ] Traffic stats are collected
- [ ] Everything survives reboot

**If all checked: Congratulations! 🎉**

Your WiFi Monitor hotspot is fully operational!

---

**Need Help?**
- Check logs: `sudo journalctl -u wifi-monitor -f`
- Run tests: `bash test-hotspot.sh`
- Review architecture: `NETWORK_ARCHITECTURE.md`
