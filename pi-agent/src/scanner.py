"""Network scanner - supports both simulation and real scanning."""
import random
import subprocess
import socket
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path


logger = logging.getLogger(__name__)


class NetworkScanner:
    def __init__(self, simulation_mode: bool = False, interface: str = "wlan0", hotspot_mode: bool = False):
        self.simulation_mode = simulation_mode
        self.interface = interface
        self.hotspot_mode = hotspot_mode
        self._simulated_devices = []
        self._oui_database = {}
        self._load_oui_database()
    
    def scan(self, device_count: int = 5) -> List[Dict[str, Any]]:
        """Scan network for devices. Returns list of device dicts."""
        if self.simulation_mode:
            return self._simulate_devices(device_count)
        else:
            return self._real_scan()
    
    def _simulate_devices(self, count: int) -> List[Dict[str, Any]]:
        """Generate fake devices for POC testing."""
        if not self._simulated_devices:
            # Generate devices once and reuse (consistent MAC addresses)
            manufacturers = ["Apple", "Samsung", "Intel", "TP-Link", "Amazon", "Google"]
            device_types = ["smartphone", "laptop", "tablet", "smart_tv", "iot_device", "router"]
            
            for i in range(count):
                mac = self._generate_mac()
                self._simulated_devices.append({
                    "mac_address": mac,
                    "ip_address": f"192.168.1.{100 + i}",
                    "hostname": f"device-{i+1}.local",
                    "manufacturer": random.choice(manufacturers),
                    "device_type": random.choice(device_types)
                })
        
        return self._simulated_devices
    
    def _generate_mac(self) -> str:
        """Generate a random MAC address."""
        return ":".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
    
    def _real_scan(self) -> List[Dict[str, Any]]:
        """
        Real network scanning using multiple methods.
        
        Priority order:
        1. Read from /proc/net/arp (passive, no root required)
        2. Use arp-scan if available (active, requires root)
        3. Use nmap if available (active, requires root)
        """
        devices = []

        # Hotspot mode: prefer DHCP leases and neighbor table
        if self.hotspot_mode:
            devices = self._scan_hotspot_clients()
        
        # Method 1: Read ARP table (works without root)
        if not devices:
            devices = self._scan_arp_table()
        
        # Method 2: If ARP table is empty or we need more info, try arp-scan
        if not devices:
            devices = self._scan_with_arp_scan()
        
        # Method 3: Fallback to nmap
        if not devices:
            devices = self._scan_with_nmap()
        
        # Enhance device information
        for device in devices:
            # Resolve hostname if IP is known
            if device.get("ip_address"):
                device["hostname"] = self._resolve_hostname(device["ip_address"])
            # Lookup manufacturer
            device["manufacturer"] = self._lookup_manufacturer(device["mac_address"])
            # Guess device type (basic heuristics)
            device["device_type"] = self._guess_device_type(device)
        
        logger.info(f"Scanned {len(devices)} devices on network")
        return devices

    def _scan_hotspot_clients(self) -> List[Dict[str, Any]]:
        """Scan hotspot clients using DHCP leases and neighbor table."""
        devices = []

        leases = self._scan_dnsmasq_leases()
        neighbors = self._scan_ip_neigh()
        stations = self._scan_iw_station_dump()

        # Merge by MAC address, preferring lease data for hostname/IP
        merged = {}
        for device in stations + neighbors + leases:
            mac = device.get("mac_address")
            if not mac:
                continue
            mac = mac.upper()
            existing = merged.get(mac, {})
            merged[mac] = {
                "mac_address": mac,
                "ip_address": device.get("ip_address") or existing.get("ip_address"),
                "hostname": device.get("hostname") or existing.get("hostname"),
                "manufacturer": device.get("manufacturer") or existing.get("manufacturer"),
                "device_type": device.get("device_type") or existing.get("device_type") or "unknown",
            }

        devices = list(merged.values())
        logger.info(f"Hotspot scan found {len(devices)} devices")
        return devices

    def _scan_dnsmasq_leases(self) -> List[Dict[str, Any]]:
        """Read DHCP leases from dnsmasq for hotspot clients."""
        devices = []
        lease_files = [
            Path("/var/lib/misc/dnsmasq.leases"),
            Path("/var/lib/dnsmasq/dnsmasq.leases"),
        ]

        lease_file = next((p for p in lease_files if p.exists()), None)
        if not lease_file:
            return devices

        try:
            with open(lease_file, "r") as f:
                for line in f:
                    # Format: <expiry> <mac> <ip> <hostname> <clientid>
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        mac = parts[1].upper()
                        ip = parts[2]
                        hostname = parts[3] if parts[3] != "*" else None
                        devices.append({
                            "mac_address": mac,
                            "ip_address": ip,
                            "hostname": hostname,
                            "manufacturer": None,
                            "device_type": "unknown",
                        })
        except Exception as e:
            logger.error(f"Error reading dnsmasq leases: {e}")

        return devices

    def _scan_ip_neigh(self) -> List[Dict[str, Any]]:
        """Read neighbor table for the hotspot interface."""
        devices = []

        try:
            cmd = ["ip", "neigh", "show", "dev", self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return devices

            for line in result.stdout.split("\n"):
                # Example: 192.168.50.23 lladdr AA:BB:CC:DD:EE:FF REACHABLE
                match = re.search(r"(\d+\.\d+\.\d+\.\d+).*lladdr\s+([0-9A-Fa-f:]{17})", line)
                if match:
                    ip, mac = match.groups()
                    devices.append({
                        "mac_address": mac.upper(),
                        "ip_address": ip,
                        "hostname": None,
                        "manufacturer": None,
                        "device_type": "unknown",
                    })
        except Exception as e:
            logger.error(f"Error reading neighbor table: {e}")

        return devices

    def _scan_iw_station_dump(self) -> List[Dict[str, Any]]:
        """Read connected station MACs from iw for the hotspot interface."""
        devices = []

        try:
            cmd = ["iw", "dev", self.interface, "station", "dump"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return devices

            for line in result.stdout.split("\n"):
                match = re.match(r"^Station\s+([0-9A-Fa-f:]{17})\s+", line)
                if match:
                    mac = match.group(1).upper()
                    devices.append({
                        "mac_address": mac,
                        "ip_address": None,
                        "hostname": None,
                        "manufacturer": None,
                        "device_type": "unknown",
                    })
        except FileNotFoundError:
            logger.warning("iw not installed")
        except Exception as e:
            logger.error(f"Error reading iw station dump: {e}")

        return devices
    
    def _scan_arp_table(self) -> List[Dict[str, Any]]:
        """Read devices from Linux ARP table (no root required)."""
        devices = []
        arp_file = Path("/proc/net/arp")
        
        if not arp_file.exists():
            logger.warning("/proc/net/arp not found (not on Linux?)")
            return devices
        
        try:
            with open(arp_file, 'r') as f:
                lines = f.readlines()[1:]  # Skip header
                
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        ip = parts[0]
                        mac = parts[3]
                        
                        # Filter out invalid/incomplete entries
                        if mac != "00:00:00:00:00:00" and ":" in mac:
                            devices.append({
                                "mac_address": mac.upper(),
                                "ip_address": ip,
                                "hostname": None,
                                "manufacturer": None,
                                "device_type": "unknown"
                            })
            
            logger.info(f"Found {len(devices)} devices in ARP table")
        except Exception as e:
            logger.error(f"Error reading ARP table: {e}")
        
        return devices
    
    def _scan_with_arp_scan(self) -> List[Dict[str, Any]]:
        """Scan network using arp-scan (requires root and arp-scan installed)."""
        devices = []
        
        try:
            # Get network info from interface
            network = self._get_network_cidr()
            if not network:
                logger.warning("Could not determine network CIDR")
                return devices
            
            # Run arp-scan
            cmd = ["sudo", "arp-scan", "--interface", self.interface, "--localnet"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                logger.warning(f"arp-scan failed: {result.stderr}")
                return devices
            
            # Parse output
            for line in result.stdout.split('\n'):
                # Format: IP    MAC    Vendor
                match = re.match(r'(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F:]{17})\s*(.*)', line)
                if match:
                    ip, mac, vendor = match.groups()
                    devices.append({
                        "mac_address": mac.upper(),
                        "ip_address": ip,
                        "hostname": None,
                        "manufacturer": vendor.strip() or None,
                        "device_type": "unknown"
                    })
            
            logger.info(f"arp-scan found {len(devices)} devices")
        except FileNotFoundError:
            logger.warning("arp-scan not installed")
        except subprocess.TimeoutExpired:
            logger.error("arp-scan timeout")
        except Exception as e:
            logger.error(f"Error running arp-scan: {e}")
        
        return devices
    
    def _scan_with_nmap(self) -> List[Dict[str, Any]]:
        """Scan network using nmap (requires nmap installed)."""
        devices = []
        
        try:
            network = self._get_network_cidr()
            if not network:
                return devices
            
            # Run nmap for ARP discovery
            cmd = ["sudo", "nmap", "-sn", "-PR", network]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.warning(f"nmap failed: {result.stderr}")
                return devices
            
            # Parse nmap output
            current_ip = None
            for line in result.stdout.split('\n'):
                # Look for IP addresses
                ip_match = re.search(r'Nmap scan report for (\d+\.\d+\.\d+\.\d+)', line)
                if ip_match:
                    current_ip = ip_match.group(1)
                
                # Look for MAC addresses
                mac_match = re.search(r'MAC Address: ([0-9A-F:]{17})', line, re.IGNORECASE)
                if mac_match and current_ip:
                    devices.append({
                        "mac_address": mac_match.group(1).upper(),
                        "ip_address": current_ip,
                        "hostname": None,
                        "manufacturer": None,
                        "device_type": "unknown"
                    })
                    current_ip = None
            
            logger.info(f"nmap found {len(devices)} devices")
        except FileNotFoundError:
            logger.warning("nmap not installed")
        except subprocess.TimeoutExpired:
            logger.error("nmap timeout")
        except Exception as e:
            logger.error(f"Error running nmap: {e}")
        
        return devices
    
    def _get_network_cidr(self) -> Optional[str]:
        """Get network CIDR from interface."""
        try:
            cmd = ["ip", "-o", "-f", "inet", "addr", "show", self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Parse output: "2: wlan0    inet 192.168.1.10/24 ..."
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+/\d+)', result.stdout)
                if match:
                    cidr = match.group(1)
                    # Convert to network address
                    ip, prefix = cidr.split('/')
                    octets = ip.split('.')
                    octets[-1] = '0'  # Set host part to 0
                    network = '.'.join(octets) + '/' + prefix
                    return network
        except Exception as e:
            logger.error(f"Error getting network CIDR: {e}")
        
        return None
    
    def _resolve_hostname(self, ip: str) -> Optional[str]:
        """Resolve hostname from IP address."""
        try:
            hostname = socket.gethostbyaddr(ip)[0]
            return hostname
        except (socket.herror, socket.gaierror, socket.timeout):
            return None
    
    def _lookup_manufacturer(self, mac: str) -> Optional[str]:
        """Lookup manufacturer from MAC OUI."""
        if not mac:
            return None
        
        # Get first 3 octets (OUI)
        oui = mac.upper().replace(':', '').replace('-', '')[:6]
        return self._oui_database.get(oui, None)
    
    def _load_oui_database(self):
        """Load OUI database (IEEE manufacturer mappings)."""
        # Prefer system OUI database if available; fall back to embedded sample.
        if self._load_oui_from_system():
            return

        # Simple embedded database with common manufacturers
        # In production, you'd download this from IEEE or use a library
        self._oui_database = {
            "000D93": "Apple",
            "001124": "Apple",
            "0017F2": "Apple",
            "001CB3": "Apple",
            "003093": "Apple",
            "0050E4": "Apple",
            "7C04D0": "Apple",
            "A82066": "Apple",
            "F0DCE2": "Apple",
            "002566": "Samsung",
            "0026FC": "Samsung",
            "0027E3": "Samsung",
            "30D6C9": "Samsung",
            "38AA3C": "Samsung",
            "B4F0AB": "Samsung",
            "C8F230": "Samsung",
            "4C3BD6": "Samsung",
            "00B362": "Intel",
            "087211": "Intel",
            "D85D4C": "Intel",
            "2C6E85": "TP-Link",
            "F09FC2": "TP-Link",
            "B0487A": "TP-Link",
            "F4EC38": "Amazon",
            "747548": "Amazon",
            "78E103": "Amazon",
            "3CE8EB": "Google",
            "F4F5D8": "Google",
            "A0ED4E": "Google",
        }

    def _load_oui_from_system(self) -> bool:
        """Load OUI mappings from common system files if present."""
        candidates = [
            Path("/usr/share/ieee-data/oui.txt"),
            Path("/usr/share/ieee-data/oui.csv"),
            Path("/var/lib/ieee-data/oui.txt"),
            Path("/usr/share/misc/oui.txt"),
        ]

        for path in candidates:
            if path.exists():
                try:
                    count = self._parse_oui_file(path)
                    if count > 0:
                        logger.info(f"Loaded {count} OUIs from {path}")
                        return True
                except Exception as e:
                    logger.warning(f"Failed to read OUI file {path}: {e}")

        return False

    def _parse_oui_file(self, path: Path) -> int:
        """Parse OUI file formats (txt/csv) into the OUI database."""
        self._oui_database = {}
        count = 0

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if path.suffix.lower() == ".csv":
                    # Format: "OUI","Company Name","Company Address"
                    if line.startswith("\""):
                        parts = [p.strip('"') for p in line.split(",")]
                        if parts and len(parts[0]) >= 6:
                            oui = parts[0].replace(":", "").replace("-", "")[:6].upper()
                            vendor = parts[1] if len(parts) > 1 else ""
                            if len(oui) == 6 and vendor:
                                self._oui_database[oui] = vendor
                                count += 1
                    continue

                # Common txt format: "FC-34-97   (hex)            Intel Corporate"
                if "(hex)" in line:
                    parts = line.split("(hex)")
                    if len(parts) >= 2:
                        oui_part = parts[0].strip()
                        vendor = parts[1].strip()
                        oui = oui_part.replace("-", "").replace(":", "").upper()
                        if len(oui) == 6 and vendor:
                            self._oui_database[oui] = vendor
                            count += 1
                    continue

                # Alternative txt format: "FC3497     Intel Corporate"
                if len(line) >= 6 and line[:6].isalnum():
                    oui = line[:6].replace("-", "").replace(":", "").upper()
                    vendor = line[6:].strip()
                    if len(oui) == 6 and vendor:
                        self._oui_database[oui] = vendor
                        count += 1

        return count
    
    def _guess_device_type(self, device: Dict[str, Any]) -> str:
        """Guess device type based on hostname and manufacturer."""
        hostname = (device.get("hostname") or "").lower()
        manufacturer = (device.get("manufacturer") or "").lower()
        
        # Check hostname patterns
        if "router" in hostname or "gateway" in hostname:
            return "router"
        elif "phone" in hostname or "iphone" in hostname or "android" in hostname:
            return "smartphone"
        elif "laptop" in hostname or "macbook" in hostname or "thinkpad" in hostname:
            return "laptop"
        elif "ipad" in hostname or "tablet" in hostname:
            return "tablet"
        elif "tv" in hostname or "roku" in hostname or "chromecast" in hostname:
            return "smart_tv"
        elif "echo" in hostname or "alexa" in hostname or "nest" in hostname:
            return "iot_device"
        
        # Check manufacturer
        if "apple" in manufacturer:
            # Apple makes mostly phones, laptops, tablets
            return "smartphone"
        elif "samsung" in manufacturer:
            return "smartphone"
        elif any(vendor in manufacturer for vendor in [
            "tp-link", "tplink", "netgear", "d-link", "dlink", "asus", "ubiquiti", "mikrotik"
        ]):
            return "router"
        elif "amazon" in manufacturer:
            return "iot_device"
        elif "google" in manufacturer:
            return "iot_device"
        
        return "unknown"
