# WiFi Monitor Pi Agent - Setup Guide

Complete guide for installing and configuring the WiFi Monitor agent on Raspberry Pi.

## Table of Contents

1. [Hardware Requirements](#hardware-requirements)
2. [Software Requirements](#software-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Running the Agent](#running-the-agent)
6. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
7. [Advanced Configuration](#advanced-configuration)
8. [Security Considerations](#security-considerations)

---

## Hardware Requirements

### Minimum Requirements
- **Raspberry Pi 3B or newer** (Pi 4 recommended for better performance)
- **microSD card**: 8GB minimum (16GB+ recommended)
- **Power supply**: Official Raspberry Pi power adapter
- **Network**: WiFi or Ethernet connection to your network

### Recommended Setup
- Raspberry Pi 4 (2GB+ RAM)
- 32GB microSD card (Class 10 or better)
- Ethernet connection for initial setup
- Case with cooling (heatsinks or fan)

### Network Requirements
- The Raspberry Pi should be connected to the same network you want to monitor
- For WiFi monitoring: Pi should have WiFi enabled (wlan0 interface)
- For Ethernet monitoring: Use eth0 interface
- Access to the backend server (running on same network or accessible via internet)

---

## Software Requirements

### Operating System
- **Raspberry Pi OS** (formerly Raspbian) - Lite or Desktop version
- Based on Debian 11 (Bullseye) or newer
- 32-bit or 64-bit supported

### Download Raspberry Pi OS
```bash
# Download from official site:
# https://www.raspberrypi.com/software/operating-systems/

# Recommended: Raspberry Pi OS Lite (64-bit) for headless setup
```

### Initial Pi Setup

1. **Flash OS to SD card** using Raspberry Pi Imager
2. **Enable SSH** (create empty file named `ssh` in boot partition)
3. **Configure WiFi** (optional - create `wpa_supplicant.conf` in boot partition):
   ```conf
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1

   network={
       ssid="Your_WiFi_SSID"
       psk="Your_WiFi_Password"
       key_mgmt=WPA-PSK
   }
   ```

4. **First boot setup**:
   ```bash
   # SSH into your Pi
   ssh pi@raspberrypi.local
   # Default password: raspberry

   # Change default password
   passwd

   # Update system
   sudo apt update
   sudo apt upgrade -y

   # Set timezone
   sudo raspi-config
   # Navigate to: Localisation Options > Timezone

   # Set hostname (optional)
   sudo raspi-config
   # Navigate to: System Options > Hostname
   # Suggested: wifi-monitor
   ```

---

## Installation

### Method 1: Automated Installation (Recommended)

1. **Download the agent**:
   ```bash
   cd ~
   git clone <your-repo-url> wifi-monitor
   cd wifi-monitor/pi-agent
   ```

2. **Run the installation script**:
   ```bash
   sudo bash install.sh
   ```

   The script will:
   - Install system dependencies (Python, arp-scan, nmap, iptables)
   - Create a dedicated user account (`wifi-monitor`)
   - Set up Python virtual environment
   - Install Python packages
   - Configure sudo permissions for network tools
   - Install systemd service
   - Set up log rotation

3. **Follow the post-installation instructions** displayed by the script

### Method 2: Manual Installation

If you prefer manual installation or need to customize:

1. **Install system dependencies**:
   ```bash
   sudo apt update
   sudo apt install -y \
       python3 \
       python3-pip \
       python3-venv \
       arp-scan \
       nmap \
       iptables \
       iptables-persistent \
       net-tools \
       iproute2 \
       git
   ```

2. **Create service user**:
   ```bash
   sudo useradd -r -s /bin/bash -d /opt/wifi-monitor -m wifi-monitor
   ```

3. **Set up application directory**:
   ```bash
   sudo mkdir -p /opt/wifi-monitor
   sudo cp -r src run.py requirements.txt config.yaml /opt/wifi-monitor/
   sudo mkdir -p /opt/wifi-monitor/logs
   sudo chown -R wifi-monitor:wifi-monitor /opt/wifi-monitor
   ```

4. **Create Python virtual environment**:
   ```bash
   cd /opt/wifi-monitor
   sudo -u wifi-monitor python3 -m venv venv
   sudo -u wifi-monitor venv/bin/pip install --upgrade pip
   sudo -u wifi-monitor venv/bin/pip install -r requirements.txt
   ```

5. **Configure sudo permissions**:
   ```bash
   sudo nano /etc/sudoers.d/wifi-monitor
   ```
   Add:
   ```
   wifi-monitor ALL=(ALL) NOPASSWD: /usr/bin/arp-scan
   wifi-monitor ALL=(ALL) NOPASSWD: /usr/sbin/arp-scan
   wifi-monitor ALL=(ALL) NOPASSWD: /usr/bin/nmap
   wifi-monitor ALL=(ALL) NOPASSWD: /usr/sbin/iptables
   wifi-monitor ALL=(ALL) NOPASSWD: /sbin/iptables
   ```
   ```bash
   sudo chmod 440 /etc/sudoers.d/wifi-monitor
   ```

6. **Install systemd service** (see [systemd/wifi-monitor.service](systemd/wifi-monitor.service))

---

## Configuration

### Edit Configuration File

```bash
sudo nano /opt/wifi-monitor/config.yaml
```

### Configuration Options

```yaml
# Backend API endpoint - REQUIRED
# Point to your backend server
api_base_url: "http://192.168.1.100:5000/api/v1"

# Network interface to monitor - REQUIRED
# wlan0 for WiFi, eth0 for Ethernet
interface: "wlan0"

# Authentication credentials - REQUIRED
# Use credentials from your backend admin account
auth:
  email: "admin@wifi.com"
  password: "admin123"

# Simulation mode - IMPORTANT
# Set to false for production on Raspberry Pi
simulation_mode: false

# Scan interval (seconds)
# How often to scan for new devices
scan_interval: 30

# Stats collection interval (seconds)
# How often to collect usage statistics
stats_interval: 60

# Logging
log_level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
log_dir: "logs"

# Network retry configuration
retry_attempts: 3
retry_delay: 5
```

### Critical Settings for Production

**⚠️ MUST CHANGE:**
1. `api_base_url`: Your backend server IP/hostname
2. `auth.email`: Your admin email
3. `auth.password`: Your admin password
4. `simulation_mode`: Set to `false` for real monitoring
5. `interface`: Set to your network interface (check with `ip addr`)

### Test Configuration

Before starting the service, test your configuration:

```bash
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config
```

This will validate:
- Configuration file syntax
- Backend connectivity
- Authentication credentials
- Network interface availability

---

## Running the Agent

### Start the Service

```bash
# Enable service to start on boot
sudo systemctl enable wifi-monitor

# Start the service
sudo systemctl start wifi-monitor

# Check status
sudo systemctl status wifi-monitor
```

### Stop the Service

```bash
sudo systemctl stop wifi-monitor
```

### Restart the Service

```bash
sudo systemctl restart wifi-monitor
```

### Disable Auto-Start

```bash
sudo systemctl disable wifi-monitor
```

---

## Monitoring & Troubleshooting

### View Logs

**System logs (journalctl)**:
```bash
# View all logs
sudo journalctl -u wifi-monitor

# Follow logs in real-time
sudo journalctl -u wifi-monitor -f

# View last 100 lines
sudo journalctl -u wifi-monitor -n 100

# View logs from today
sudo journalctl -u wifi-monitor --since today
```

**Application logs**:
```bash
# View main log
tail -f /opt/wifi-monitor/logs/agent_*.log

# View error log
tail -f /opt/wifi-monitor/logs/agent_errors_*.log

# View all logs
ls -lh /opt/wifi-monitor/logs/
```

### Common Issues

#### 1. Agent won't start

**Check status**:
```bash
sudo systemctl status wifi-monitor
```

**Possible causes**:
- Configuration errors
- Backend server not reachable
- Invalid credentials
- Missing dependencies

**Solution**:
```bash
# Test configuration
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config

# Check backend connectivity
curl http://your-backend-url:5000/api/v1/system/health
```

#### 2. No devices found

**Check network scanning**:
```bash
# Test ARP table
cat /proc/net/arp

# Test arp-scan (requires sudo)
sudo arp-scan --interface=wlan0 --localnet

# Check interface status
ip addr show wlan0
```

**Possible causes**:
- Wrong interface specified
- Interface not connected
- No other devices on network
- Permission issues

**Solution**:
- Verify `interface` in config.yaml
- Ensure Pi is connected to network
- Check sudo permissions

#### 3. Stats collection fails

**Check iptables**:
```bash
# View iptables rules
sudo iptables -L -n -v

# Check if custom chains exist
sudo iptables -L WIFI_MONITOR_OUT -n -v
sudo iptables -L WIFI_MONITOR_IN -n -v
```

**Possible causes**:
- Insufficient permissions
- iptables not available
- Firewall interference

**Solution**:
- Verify sudo permissions are configured
- Check if iptables-persistent is installed
- Review error logs

#### 4. Authentication failed

**Possible causes**:
- Wrong credentials
- Backend server not running
- Network connectivity issues
- User account not created in backend

**Solution**:
1. Verify credentials in config.yaml
2. Check backend is running: `curl http://backend:5000/api/v1/system/health`
3. Ensure user account exists in backend
4. Check backend logs for authentication errors

### Performance Monitoring

**Check resource usage**:
```bash
# CPU and memory usage
top -b -n 1 | grep python3

# Systemd resource usage
systemctl status wifi-monitor

# Disk space
df -h /opt/wifi-monitor/logs/

# Network connectivity
ping your-backend-server
```

**Optimal performance**:
- CPU usage: < 5%
- Memory usage: ~50-100MB
- Network: minimal bandwidth usage
- Logs: rotated daily, max 70MB

---

## Advanced Configuration

### Custom Scan Intervals

For networks with many devices or high activity:

```yaml
# Fast scanning (every 15 seconds)
scan_interval: 15
stats_interval: 30

# Slow scanning (every 5 minutes)
scan_interval: 300
stats_interval: 300
```

### Debug Mode

Enable detailed logging for troubleshooting:

```yaml
log_level: "DEBUG"
```

Then restart:
```bash
sudo systemctl restart wifi-monitor
```

### Multiple Interface Monitoring

To monitor both WiFi and Ethernet, run two instances:

1. Create second config:
   ```bash
   sudo cp /opt/wifi-monitor/config.yaml /opt/wifi-monitor/config-eth0.yaml
   ```

2. Edit for eth0:
   ```yaml
   interface: "eth0"
   ```

3. Create second service:
   ```bash
   sudo cp /etc/systemd/system/wifi-monitor.service /etc/systemd/system/wifi-monitor-eth0.service
   ```

4. Update ExecStart in new service to use different config

### Network Configuration for Bridge Mode

If using Pi as WiFi access point (bridge mode):

```bash
# Enable IP forwarding
echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Configure iptables for NAT
sudo iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
sudo iptables -A FORWARD -i wlan0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan0 -j ACCEPT

# Save iptables rules
sudo netfilter-persistent save
```

---

## Security Considerations

### 1. Credential Security

**Never commit credentials to version control**:
```bash
# Add config.yaml to .gitignore
echo "config.yaml" >> .gitignore
```

**Use environment variables** (optional):
```bash
# Create .env file
echo "BACKEND_EMAIL=admin@wifi.com" > /opt/wifi-monitor/.env
echo "BACKEND_PASSWORD=secure_password" >> /opt/wifi-monitor/.env
sudo chmod 600 /opt/wifi-monitor/.env
```

### 2. File Permissions

```bash
# Verify correct permissions
ls -la /opt/wifi-monitor/

# config.yaml should be readable only by wifi-monitor user
sudo chmod 600 /opt/wifi-monitor/config.yaml
sudo chown wifi-monitor:wifi-monitor /opt/wifi-monitor/config.yaml
```

### 3. Network Security

- Use HTTPS for backend API (configure reverse proxy)
- Consider VPN for remote backend access
- Use strong passwords
- Regularly update system packages

### 4. Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow backend connectivity (if local)
sudo ufw allow from 192.168.1.0/24

# Enable firewall
sudo ufw enable
```

### 5. Regular Updates

```bash
# Update Raspberry Pi OS
sudo apt update
sudo apt upgrade -y

# Update Python packages
cd /opt/wifi-monitor
sudo -u wifi-monitor venv/bin/pip install --upgrade -r requirements.txt

# Restart service
sudo systemctl restart wifi-monitor
```

---

## Uninstallation

To completely remove the agent:

```bash
# Stop and disable service
sudo systemctl stop wifi-monitor
sudo systemctl disable wifi-monitor

# Remove service file
sudo rm /etc/systemd/system/wifi-monitor.service
sudo systemctl daemon-reload

# Remove application
sudo rm -rf /opt/wifi-monitor

# Remove user
sudo userdel wifi-monitor

# Remove sudo configuration
sudo rm /etc/sudoers.d/wifi-monitor

# Remove log rotation
sudo rm /etc/logrotate.d/wifi-monitor

# (Optional) Remove system packages
sudo apt remove --purge arp-scan nmap iptables-persistent
sudo apt autoremove -y
```

---

## Additional Resources

- **Project Documentation**: See main README.md
- **API Reference**: docs/API_REFERENCE.md
- **Backend Setup**: backend/README.md
- **Troubleshooting**: Check logs and systemd status

## Support

For issues and questions:
1. Check logs: `sudo journalctl -u wifi-monitor -f`
2. Verify configuration: `run.py --test-config`
3. Review this guide
4. Check backend server logs
5. Open an issue in the project repository

---

**Version**: 1.0.0  
**Last Updated**: March 2026  
**Compatibility**: Raspberry Pi 3B+, 4, 5 | Raspberry Pi OS (Debian 11+)
