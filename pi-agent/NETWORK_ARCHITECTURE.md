# WiFi Monitor - Network Architecture & Setup Flow

## 🌐 Network Architecture

### Access Point (Hotspot) Mode - **RECOMMENDED SETUP**

This is the architecture you're implementing where the Raspberry Pi acts as a WiFi hotspot.

```
                         Internet (4G/Cable/Fiber)
                                    │
                                    ▼
                ┌───────────────────────────────────┐
                │      Router / Modem               │
                │     (Your ISP Equipment)          │
                └───────────────────────────────────┘
                                    │
                                    │ Ethernet Cable
                                    ▼
          ┌──────────────────────────────────────────────┐
          │        Raspberry Pi (WiFi Monitor)           │
          │                                              │
          │  ┌────────────┐        ┌──────────────┐     │
          │  │    eth0    │◄──────►│  Processing  │     │
          │  │  (INPUT)   │        │  & NAT       │     │
          │  └────────────┘        └──────────────┘     │
          │                              │               │
          │                              ▼               │
          │  ┌────────────┐        ┌──────────────┐     │
          │  │   wlan0    │◄──────►│   Monitor    │     │
          │  │ (HOTSPOT)  │        │   Agent      │     │
          │  └────────────┘        └──────────────┘     │
          └──────────────────────────────────────────────┘
                     │ WiFi Signal
                     │ (192.168.50.x)
       ──────────────┴──────────────────────
       │              │              │
       ▼              ▼              ▼
   ┌────────┐   ┌────────┐   ┌────────┐
   │ Phone  │   │ Laptop │   │ Tablet │
   └────────┘   └────────┘   └────────┘
   
   All devices connect to Pi's hotspot
   Pi monitors all traffic & device info
```

### Alternative: USB Dongle for Internet

```
                         Internet (Mobile Data)
                                    │
                                    ▼
          ┌──────────────────────────────────────────────┐
          │        Raspberry Pi (WiFi Monitor)           │
          │                                              │
          │  ┌────────────┐        ┌──────────────┐     │
          │  │    usb0    │◄──────►│  Processing  │     │
          │  │ (4G Dongle)│        │  & NAT       │     │
          │  └────────────┘        └──────────────┘     │
          │                              │               │
          │                              ▼               │
          │  ┌────────────┐        ┌──────────────┐     │
          │  │   wlan0    │◄──────►│   Monitor    │     │
          │  │ (HOTSPOT)  │        │   Agent      │     │
          │  └────────────┘        └──────────────┘     │
          └──────────────────────────────────────────────┘
                     │ WiFi Signal
       ──────────────┴──────────────
       │              │
       ▼              ▼
   ┌────────┐   ┌────────┐
   │Devices │   │Devices │
   └────────┘   └────────┘
```

## 📊 Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Data Flow                               │
└─────────────────────────────────────────────────────────────┘

1. Device Connects:
   Phone ──WiFi──> Raspberry Pi (hostapd receives)
                        │
                        ▼
                   DHCP (dnsmasq assigns IP: 192.168.50.x)
                        │
                        ▼
                   Device online & reachable

2. Internet Access:
   Device Request ──> wlan0 (192.168.50.1)
                        │
                        ▼
                   iptables (NAT/MASQUERADE)
                        │
                        ▼
                   eth0 (forwards to internet)
                        │
                        ▼
                   Internet Response
                        │
                        ▼
                   eth0 ──NAT──> wlan0 ──> Device

3. Monitoring:
   Device Activity ──> wlan0 interface
                        │
                        ▼
                   Scanner (detects via ARP)
                        │
                        ▼
                   Collector (counts via iptables)
                        │
                        ▼
                   Backend API (syncs data)
                        │
                        ▼
                   Dashboard (displays info)
```

## 🔄 Setup Flow

### Phase 1: Hardware Setup
```
┌─────────────────────────────────────────┐
│ 1. Get Raspberry Pi (3B+, 4, or 5)     │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 2. Install Raspberry Pi OS              │
│    - Download from raspberrypi.com      │
│    - Flash to microSD (16GB+)           │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 3. Connect Internet Source              │
│    Option A: Ethernet cable to router   │
│    Option B: USB 4G/LTE dongle          │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 4. Power on & SSH into Pi               │
│    ssh pi@raspberrypi.local             │
└─────────────────────────────────────────┘
```

### Phase 2: Hotspot Configuration
```
┌─────────────────────────────────────────┐
│ 1. Download WiFi Monitor Agent          │
│    git clone <repo> wifi-monitor        │
│    cd wifi-monitor/pi-agent             │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 2. Run Hotspot Setup Script             │
│    sudo bash setup-hotspot.sh           │
│                                         │
│    This installs:                       │
│    - hostapd (WiFi AP software)         │
│    - dnsmasq (DHCP + DNS server)        │
│    - iptables rules (NAT)               │
│    - IP forwarding                      │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 3. Configure Hotspot Settings           │
│    Default:                             │
│    - SSID: WiFi-Monitor                 │
│    - Password: monitor123               │
│    - IP: 192.168.50.1                   │
│                                         │
│    Edit /etc/hostapd/hostapd.conf      │
│    to change settings                   │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 4. Test Hotspot                         │
│    bash test-hotspot.sh                 │
│                                         │
│    Verifies:                            │
│    - Services running                   │
│    - WiFi broadcasting                  │
│    - DHCP working                       │
│    - NAT configured                     │
│    - Internet accessible                │
└─────────────────────────────────────────┘
                │
                ▼
           ┌────────┐
           │ READY! │
           └────────┘
```

### Phase 3: Monitor Agent Setup
```
┌─────────────────────────────────────────┐
│ 1. Install WiFi Monitor Agent           │
│    sudo bash install.sh                 │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 2. Configure Agent                      │
│    sudo nano /opt/wifi-monitor/config.yaml│
│                                         │
│    Set:                                 │
│    - api_base_url: <backend URL>        │
│    - auth: <credentials>                │
│    - interface: wlan0                   │
│    - hotspot_mode: true                 │
│    - simulation_mode: false             │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 3. Start Monitoring Service             │
│    systemctl enable wifi-monitor        │
│    systemctl start wifi-monitor         │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 4. Verify Monitoring                    │
│    journalctl -u wifi-monitor -f        │
│                                         │
│    Should see:                          │
│    - Authentication success             │
│    - Devices being scanned              │
│    - Stats being collected              │
│    - Data syncing to backend            │
└─────────────────────────────────────────┘
```

### Phase 4: Connect Devices
```
┌─────────────────────────────────────────┐
│ 1. Find WiFi Network                    │
│    Look for: WiFi-Monitor               │
│    (or your custom SSID)                │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 2. Connect with Password                │
│    Default: monitor123                  │
│    (or your custom password)            │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 3. Device Gets IP via DHCP              │
│    Range: 192.168.50.10 - .250          │
│    Gateway: 192.168.50.1 (the Pi)       │
│    DNS: 192.168.50.1 (dnsmasq)          │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 4. Test Internet Access                 │
│    Open browser, visit website          │
│    Internet should work normally        │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ 5. Device Appears in Monitor            │
│    - Detected via ARP table             │
│    - MAC address identified             │
│    - Manufacturer looked up             │
│    - Traffic monitoring begins          │
│    - Data synced to backend             │
└─────────────────────────────────────────┘
```

## 🧪 Testing Flow

```
┌─────────────────────────────────────────┐
│ Test 1: Hotspot Is Running              │
│ Command: systemctl status hostapd       │
│ Expected: active (running)              │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Test 2: WiFi Is Broadcasting            │
│ Command: iwconfig wlan0                 │
│ Expected: Mode:Master, ESSID shown      │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Test 3: DHCP Is Working                 │
│ Command: systemctl status dnsmasq       │
│ Expected: active (running)              │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Test 4: NAT Is Configured               │
│ Command: iptables -t nat -L             │
│ Expected: MASQUERADE rule visible      │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Test 5: Device Can Connect              │
│ Action: Connect phone to WiFi           │
│ Expected: Gets IP, has internet         │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Test 6: Device Is Detected              │
│ Command: cat /proc/net/arp              │
│ Expected: Device MAC/IP listed          │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Test 7: Monitoring Is Working           │
│ Command: journalctl -u wifi-monitor     │
│ Expected: Devices scanned, stats sent   │
└─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────┐
│ Test 8: Data In Backend                 │
│ Action: Check backend dashboard         │
│ Expected: Devices visible, traffic shown│
└─────────────────────────────────────────┘
```

## 🔧 Troubleshooting Flow

```
Problem: Hotspot not visible
     │
     ▼
Check: systemctl status hostapd
     │
     ├──> Running? ──No──> journalctl -u hostapd -n 50
     │                      Check error logs
     │                      Restart: systemctl restart hostapd
     │
     └──> Running? ──Yes──> Check iwconfig wlan0
                            Ensure Mode:Master
                            Check /etc/hostapd/hostapd.conf

Problem: Device can't get IP
     │
     ▼
Check: systemctl status dnsmasq
     │
     ├──> Running? ──No──> journalctl -u dnsmasq -n 50
     │                      Check /etc/dnsmasq.conf
     │                      Restart: systemctl restart dnsmasq
     │
     └──> Running? ──Yes──> Check DHCP logs
                            tail -f /var/log/syslog | grep DHCP
                            Verify IP range in config

Problem: No internet on device
     │
     ▼
Check: cat /proc/sys/net/ipv4/ip_forward
     │
     ├──> 0 ──> echo 1 > /proc/sys/net/ipv4/ip_forward
     │           Add to /etc/sysctl.conf
     │
     └──> 1 ──> Check iptables NAT rules
                 iptables -t nat -L
                 Ensure MASQUERADE present
                 Check internet interface is UP

Problem: Devices not monitored
     │
     ▼
Check: systemctl status wifi-monitor
     │
     ├──> Not running ──> systemctl start wifi-monitor
     │                     Check logs for errors
     │
     └──> Running ──> Check config.yaml
                      Ensure interface: wlan0
                      Ensure simulation_mode: false
                      Check backend connectivity
```

## 📋 Quick Reference Commands

```bash
# Hotspot Management
hotspot-status                    # Check overall status
systemctl status hostapd          # Check AP service
systemctl status dnsmasq          # Check DHCP service
iwconfig wlan0                    # Check WiFi status
cat /proc/net/arp                 # See connected devices

# Testing
bash test-hotspot.sh              # Run all tests
ping 8.8.8.8                      # Test internet
curl http://backend:5000/api/v1/system/health  # Test backend

# Monitoring
journalctl -u wifi-monitor -f    # Watch monitor logs
tail -f /opt/wifi-monitor/logs/agent_*.log  # Application logs
cat /var/lib/misc/dnsmasq.leases # DHCP leases

# Configuration
nano /etc/hostapd/hostapd.conf   # Hotspot settings
nano /etc/dnsmasq.conf           # DHCP settings
nano /opt/wifi-monitor/config.yaml  # Monitor settings

# Restart Services
systemctl restart hostapd dnsmasq   # Restart hotspot
systemctl restart wifi-monitor      # Restart monitoring
```

## 🎯 Success Criteria

Your setup is working correctly when:

✅ Pi's WiFi is visible from other devices  
✅ Devices can connect with password  
✅ Devices get IP addresses (192.168.50.x)  
✅ Devices have internet access  
✅ Devices appear in ARP table  
✅ Monitor agent is running  
✅ Devices show up in backend  
✅ Traffic stats are collected  
✅ Data syncs to backend regularly  

---

**See HOTSPOT_SETUP.md for detailed step-by-step instructions.**
