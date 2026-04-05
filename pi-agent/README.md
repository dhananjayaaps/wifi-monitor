# WiFi Monitor - Raspberry Pi Agent

Production-ready network monitoring agent for Raspberry Pi that performs real-time device discovery and traffic monitoring.

## 📡 Two Operating Modes

### 🔥 **Hotspot Mode (RECOMMENDED)** - NEW!

Raspberry Pi acts as a WiFi Access Point:
- **Internet IN**: Ethernet or USB dongle → Raspberry Pi
- **WiFi OUT**: Pi broadcasts WiFi hotspot
- **Devices connect**: To Pi's hotspot (like a router)
- **Monitor**: All connected devices automatically

```
Internet → Pi (eth0) → WiFi Hotspot (wlan0) → Your Devices
           └─ Monitors everything
```

**Best for:** Home monitoring, controlled environments, public WiFi zones

### 📶 **Regular Mode** - Classic Setup

Raspberry Pi monitors existing network:
- Pi connects to your existing WiFi/Ethernet
- Monitors other devices on the same network
- Passive observation

**Best for:** Monitoring existing networks without changes

---

## Overview

The Pi Agent is a lightweight, efficient monitoring service designed to run on Raspberry Pi devices. It continuously scans your network for connected devices, monitors their traffic usage, and syncs data with the backend server.

### Key Features

✅ **Hotspot Mode (NEW!)**
- Turn Pi into WiFi access point
- Share internet from Ethernet or USB dongle
- Monitor all connected devices automatically
- Easy setup with automated scripts

✅ **Real Network Scanning**
- Multiple scanning methods (ARP table, arp-scan, nmap)
- Automatic fallback between methods
- Manufacturer identification via OUI lookup
- Hostname resolution
- Device type detection

✅ **Traffic Monitoring**
- Per-device bandwidth tracking using iptables
- Upload/download byte counters
- Fallback to interface-level monitoring
- Delta calculation for accurate reporting

✅ **DDoS Detection (Optional)**
- Run a local ML model to classify normal/dos/ddos
- Sends detection alerts to the backend

### Test DDoS Alerts

Use the simulation script to send fake DDoS/DOS alerts to the backend:

```bash
python scripts/simulate_ddos_alerts.py \
       --api-key <YOUR_AGENT_API_KEY> \
       --mac AA:BB:CC:DD:EE:01 \
       --count 5 \
       --repeat 2
```

✅ **Production Ready**
- Comprehensive error handling and retry logic
- Graceful shutdown and cleanup
- Automatic reconnection on connection loss
- Rotating logs with configurable levels
- systemd service integration
- Resource-efficient (minimal CPU/memory usage)

✅ **Easy Deployment**
- Automated installation script
- One-command hotspot setup
- Comprehensive setup guides
- Configuration validation
- Security hardening built-in

## 🚀 Quick Start

### Option A: Hotspot Mode (5 Minutes)

**Perfect for:** Setting up Pi as WiFi hotspot + monitor

```bash
# 1. Clone repository
cd ~
git clone <your-repo> wifi-monitor
cd wifi-monitor/pi-agent

# 2. Run complete setup wizard
sudo bash setup-complete.sh
```

The wizard will ask for:
- Hotspot SSID and password
- Backend server URL
- Admin credentials

**That's it!** Connect devices to your new WiFi hotspot.

📖 **Detailed Guide:** [HOTSPOT_SETUP.md](HOTSPOT_SETUP.md)

### Option B: Regular Mode (Classic)

**Perfect for:** Monitoring existing network

```bash
# 1. Install agent
cd ~/wifi-monitor/pi-agent
sudo bash install.sh

# 2. Configure
sudo nano /opt/wifi-monitor/config.yaml
# Set: api_base_url, auth, interface, simulation_mode: false

# 3. Start
sudo systemctl enable wifi-monitor
sudo systemctl start wifi-monitor
```

📖 **Detailed Guide:** [SETUP_GUIDE.md](SETUP_GUIDE.md)

---

## 📚 Documentation

- **[HOTSPOT_SETUP.md](HOTSPOT_SETUP.md)** - Complete hotspot setup guide (RECOMMENDED)
- **[NETWORK_ARCHITECTURE.md](NETWORK_ARCHITECTURE.md)** - Network diagrams and flows
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Regular mode setup (60+ pages)
- **[QUICKREF.md](QUICKREF.md)** - Command reference cheat sheet
- **[CHANGELOG.md](CHANGELOG.md)** - What's new
- **[PRODUCTION_READY.md](PRODUCTION_READY.md)** - Feature overview

---

## Architecture

### Hotspot Mode Architecture
```
                   Internet
                       │
                       ▼
┌──────────────────────────────────────────┐
│         Raspberry Pi                     │
│                                          │
│  eth0/usb0 ◄──── Internet Source        │
│      │                                   │
│      ├─ NAT/Forwarding                   │
│      │                                   │
│  wlan0 ───► WiFi Hotspot (192.168.50.x) │
│      │                                   │
│      ├─ hostapd (broadcasts WiFi)        │
│      ├─ dnsmasq (DHCP/DNS)              │
│      ├─ Scanner (detects devices)        │
│      └─ Collector (monitors traffic)     │
│                                          │
└──────────────────────────────────────────┘
       │
       └─► Client Devices (phones, laptops)
              │
              └─► Send data to Backend
```

### Regular Mode Architecture (Classic)
```
┌─────────────────────────────────────────┐
│         Raspberry Pi Agent              │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌──────────────┐   │
│  │   Scanner   │───▶│  Collector   │   │
│  │  (devices)  │    │   (stats)    │   │
│  └─────────────┘    └──────────────┘   │
│         │                   │           │
│         ▼                   ▼           │
│  ┌─────────────────────────────────┐   │
│  │       Backend Client            │   │
│  │   (API communication)           │   │
│  └─────────────────────────────────┘   │
│                  │                      │
└──────────────────┼──────────────────────┘
                   │
                   ▼
         ┌──────────────────┐
         │  Backend Server  │
         │    (REST API)    │
         └──────────────────┘
```

## Directory Structure

```
pi-agent/
├── src/
│   ├── agent.py          # Main orchestration loop
│   ├── scanner.py        # Network device discovery
│   ├── collector.py      # Traffic stats collection
│   ├── client.py         # Backend API client
│   ├── config.py         # Configuration loader
│   ├── logger.py         # Logging system
│   └── main.py           # Entry point
├── systemd/
│   └── wifi-monitor.service  # systemd unit file
├── install.sh            # Automated installer
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
├── run.py                # Run script
├── SETUP_GUIDE.md        # Comprehensive setup guide
└── README.md             # This file
```

## Components

### Scanner (`scanner.py`)
- **ARP Table Reading**: Passive scanning from `/proc/net/arp` (no root required)
- **arp-scan**: Active scanning with arp-scan utility (requires root)
- **nmap**: Fallback scanning with nmap (requires root)
- **OUI Lookup**: Manufacturer identification from MAC address
- **Hostname Resolution**: DNS lookup for device names
- **Device Type Detection**: Heuristic-based device categorization

### Collector (`collector.py`)
- **iptables Monitoring**: Per-device traffic accounting via iptables chains
- **Delta Calculation**: Accurate byte counting between intervals
- **Fallback Mode**: Interface-level stats from `/proc/net/dev`
- **Upload/Download Tracking**: Separate counters for sent/received bytes
- **Automatic Cleanup**: Removes iptables rules on shutdown

### Agent (`agent.py`)
- **Main Loop**: Orchestrates scanning and collection
- **Authentication**: Automatic login and API key management
- **Retry Logic**: Configurable retry attempts with backoff
- **Health Monitoring**: Periodic connection checks
- **Graceful Shutdown**: Signal handling for clean exit
- **Error Recovery**: Automatic reconnection on failures

### Client (`client.py`)
- **REST API**: Communication with backend server
- **Authentication**: JWT token and API key handling
- **Device Sync**: Push discovered devices to backend
- **Stats Ingestion**: Send usage statistics
- **Health Checks**: Backend connectivity monitoring

## Configuration

See `config.yaml` for all options. Key settings:

| Setting | Description | Default |
|---------|-------------|---------|
| `api_base_url` | Backend server URL | http://localhost:5000/api/v1 |
| `interface` | Network interface to monitor | wlan0 |
| `simulation_mode` | Enable simulation (no real scanning) | true |
| `scan_interval` | Device scan frequency (seconds) | 30 |
| `stats_interval` | Stats collection frequency (seconds) | 60 |
| `log_level` | Logging verbosity | INFO |
| `retry_attempts` | Number of retry attempts | 3 |
| `retry_delay` | Delay between retries (seconds) | 5 |

## Requirements

### Hardware
- Raspberry Pi 3B+ or newer (Pi 4 recommended)
- 8GB+ microSD card
- Network connection (WiFi or Ethernet)

### Software
- Raspberry Pi OS (Debian 11+)
- Python 3.7+
- arp-scan or nmap
- iptables
- systemd

### Network
- Access to monitored network
- Connectivity to backend server
- (Optional) Root access for advanced features

## Installation Methods

### Method 1: Automated (Recommended)
```bash
sudo bash install.sh
```
See [SETUP_GUIDE.md](SETUP_GUIDE.md) for details.

### Method 2: Manual
Follow the manual installation steps in [SETUP_GUIDE.md](SETUP_GUIDE.md#method-2-manual-installation).

## Usage

### Command Line

```bash
# Run with default config
python3 run.py

# Specify config file
python3 run.py -c /path/to/config.yaml

# Test configuration
python3 run.py --test-config

# Show version
python3 run.py --version
```

### As Service

```bash
# Start
sudo systemctl start wifi-monitor

# Stop
sudo systemctl stop wifi-monitor

# Status
sudo systemctl status wifi-monitor

# Logs
sudo journalctl -u wifi-monitor -f
```

## Monitoring

### View Logs

```bash
# System logs (journalctl)
sudo journalctl -u wifi-monitor -f

# Application logs
tail -f /opt/wifi-monitor/logs/agent_*.log

# Error logs only
tail -f /opt/wifi-monitor/logs/agent_errors_*.log
```

### Check Status

```bash
# Service status
sudo systemctl status wifi-monitor

# Resource usage
top -b -n 1 | grep python3

# Network connectivity
ping your-backend-server
```

## Troubleshooting

### Common Issues

**Agent won't start**
```bash
# Check status
sudo systemctl status wifi-monitor

# Test config
sudo -u wifi-monitor /opt/wifi-monitor/venv/bin/python3 /opt/wifi-monitor/run.py --test-config

# Check logs
sudo journalctl -u wifi-monitor -n 50
```

**No devices found**
```bash
# Check ARP table
cat /proc/net/arp

# Test arp-scan
sudo arp-scan --interface=wlan0 --localnet

# Verify interface
ip addr show wlan0
```

**Authentication failed**
- Verify credentials in config.yaml
- Check backend is running
- Confirm user account exists in backend

**Stats collection fails**
- Verify iptables is installed
- Check sudo permissions
- Review error logs

See [SETUP_GUIDE.md](SETUP_GUIDE.md#monitoring--troubleshooting) for detailed troubleshooting.

## Development

### Local Testing

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run in simulation mode
python3 run.py
```

### Debug Mode

```yaml
# In config.yaml
log_level: "DEBUG"
simulation_mode: true
```

## Security

- Credentials stored in local config file only
- Systemd service runs as dedicated user
- Minimal sudo permissions granted
- Protected file system paths
- Network traffic encrypted (use HTTPS backend)
- Regular security updates recommended

See [SETUP_GUIDE.md](SETUP_GUIDE.md#security-considerations) for security best practices.

## Documentation

- **[SETUP_GUIDE.md](SETUP_GUIDE.md)**: Complete installation and setup guide
- **[AUTH_SETUP.md](AUTH_SETUP.md)**: Authentication configuration
- **[API docs](../docs/API_REFERENCE.md)**: Backend API reference
- **[systemd service](systemd/wifi-monitor.service)**: Service configuration

## Performance

**Typical Resource Usage:**
- CPU: 2-5%
- Memory: 50-100 MB
- Network: < 1 KB/s
- Disk: ~10 MB logs/week

**Recommended Settings:**
- Scan interval: 30-60 seconds
- Stats interval: 60-300 seconds
- Log level: INFO (DEBUG for troubleshooting)

## Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- Tests pass (when available)
- Documentation updated
- Security considerations addressed

## License

See main project LICENSE file.

## Support

For issues and questions:
1. Check [SETUP_GUIDE.md](SETUP_GUIDE.md)
2. Review logs
3. Test configuration
4. Open issue in repository

---

**Version**: 1.0.0  
**Author**: WiFi Monitor Team  
**Last Updated**: March 2026
