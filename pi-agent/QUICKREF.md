# WiFi Monitor Pi Agent - Quick Reference

Quick command reference for common operations.

## Installation

```bash
# Clone and install
git clone <repo-url> wifi-monitor
cd wifi-monitor/pi-agent
sudo bash install.sh

# Configure
sudo nano /opt/wifi-monitor/config.yaml

# Test config
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config
```

## Service Management

```bash
# Start service
sudo systemctl start wifi-monitor

# Stop service
sudo systemctl stop wifi-monitor

# Restart service
sudo systemctl restart wifi-monitor

# Enable on boot
sudo systemctl enable wifi-monitor

# Disable on boot
sudo systemctl disable wifi-monitor

# Check status
sudo systemctl status wifi-monitor
```

## Monitoring & Logs

```bash
# Follow system logs
sudo journalctl -u wifi-monitor -f

# View last 100 lines
sudo journalctl -u wifi-monitor -n 100

# View logs since today
sudo journalctl -u wifi-monitor --since today

# View application logs
tail -f /opt/wifi-monitor/logs/agent_*.log

# View error logs
tail -f /opt/wifi-monitor/logs/agent_errors_*.log

# List all logs
ls -lh /opt/wifi-monitor/logs/
```

## Configuration

```bash
# Edit config
sudo nano /opt/wifi-monitor/config.yaml

# Test config
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config

# View current config
cat /opt/wifi-monitor/config.yaml
```

## Troubleshooting

```bash
# Check service status
sudo systemctl status wifi-monitor

# View recent errors
sudo journalctl -u wifi-monitor -p err -n 50

# Test network connectivity
ping <backend-server>
curl http://<backend-server>:5000/api/v1/system/health

# Check interface
ip addr show wlan0

# Test ARP scanning
cat /proc/net/arp
sudo arp-scan --interface=wlan0 --localnet

# Check iptables rules
sudo iptables -L -n -v
sudo iptables -L WIFI_MONITOR_OUT -n -v
sudo iptables -L WIFI_MONITOR_IN -n -v

# Check resource usage
top -b -n 1 | grep python3
systemctl status wifi-monitor

# Check disk space
df -h /opt/wifi-monitor/
```

## Network Diagnostics

```bash
# List network interfaces
ip addr

# Check WiFi status
iwconfig wlan0

# Check connection
ping 8.8.8.8

# DNS resolution
nslookup <backend-server>

# Port connectivity
nc -zv <backend-server> 5000
```

## Maintenance

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Update Python packages
cd /opt/wifi-monitor
sudo -u wifi-monitor venv/bin/pip install --upgrade -r requirements.txt

# Restart after updates
sudo systemctl restart wifi-monitor

# Clear old logs (manual)
sudo rm /opt/wifi-monitor/logs/*.log.*.gz

# Check log size
du -sh /opt/wifi-monitor/logs/
```

## Advanced

```bash
# Run manually (for debugging)
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py

# Run with custom config
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py -c /path/to/config.yaml

# Enable debug logging
# Edit config.yaml: log_level: "DEBUG"
sudo systemctl restart wifi-monitor

# View environment
sudo -u wifi-monitor env

# Check permissions
ls -la /opt/wifi-monitor/
```

## Common Configuration Changes

### Change Backend URL
```bash
sudo nano /opt/wifi-monitor/config.yaml
# Update: api_base_url: "http://new-server:5000/api/v1"
sudo systemctl restart wifi-monitor
```

### Change Network Interface
```bash
sudo nano /opt/wifi-monitor/config.yaml
# Update: interface: "eth0"
sudo systemctl restart wifi-monitor
```

### Enable Production Mode
```bash
sudo nano /opt/wifi-monitor/config.yaml
# Update: simulation_mode: false
sudo systemctl restart wifi-monitor
```

### Adjust Scan Intervals
```bash
sudo nano /opt/wifi-monitor/config.yaml
# Update: scan_interval: 60
# Update: stats_interval: 120
sudo systemctl restart wifi-monitor
```

### Enable Debug Logging
```bash
sudo nano /opt/wifi-monitor/config.yaml
# Update: log_level: "DEBUG"
sudo systemctl restart wifi-monitor
```

## File Locations

- **Installation**: `/opt/wifi-monitor/`
- **Config**: `/opt/wifi-monitor/config.yaml`
- **Logs**: `/opt/wifi-monitor/logs/`
- **Service**: `/etc/systemd/system/wifi-monitor.service`
- **Sudo rules**: `/etc/sudoers.d/wifi-monitor`
- **Log rotation**: `/etc/logrotate.d/wifi-monitor`

## Quick Checks

### Is service running?
```bash
systemctl is-active wifi-monitor
```

### Is service enabled?
```bash
systemctl is-enabled wifi-monitor
```

### Last restart time?
```bash
systemctl show wifi-monitor --property=ActiveEnterTimestamp
```

### Current log file?
```bash
ls -lht /opt/wifi-monitor/logs/ | head -n 5
```

### Backend reachable?
```bash
curl -f http://<backend>:5000/api/v1/system/health && echo "✓ OK" || echo "✗ FAIL"
```

## Emergency Procedures

### Service won't start
```bash
sudo journalctl -u wifi-monitor -n 50 --no-pager
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config
```

### High CPU usage
```bash
# Check current process
top -b -n 1 | grep python3
# Restart service
sudo systemctl restart wifi-monitor
```

### Disk full from logs
```bash
# Check log size
du -sh /opt/wifi-monitor/logs/
# Remove old compressed logs
sudo rm /opt/wifi-monitor/logs/*.gz
# Force log rotation
sudo logrotate -f /etc/logrotate.d/wifi-monitor
```

### Can't connect to backend
```bash
# Check network
ping <backend-server>
# Check backend is running
curl http://<backend-server>:5000/api/v1/system/health
# Check credentials in config
sudo cat /opt/wifi-monitor/config.yaml | grep -A3 "auth:"
```

## Uninstall

```bash
sudo systemctl stop wifi-monitor
sudo systemctl disable wifi-monitor
sudo rm /etc/systemd/system/wifi-monitor.service
sudo systemctl daemon-reload
sudo rm -rf /opt/wifi-monitor
sudo userdel wifi-monitor
sudo rm /etc/sudoers.d/wifi-monitor
sudo rm /etc/logrotate.d/wifi-monitor
```

---

**For detailed information, see [SETUP_GUIDE.md](SETUP_GUIDE.md)**
