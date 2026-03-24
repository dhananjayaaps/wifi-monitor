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
    def __init__(self, simulation_mode: bool = False, interface: str = "wlan0"):
        self.simulation_mode = simulation_mode
        self.interface = interface
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
        
        # Method 1: Read ARP table (works without root)
        devices = self._scan_arp_table()
        
        # Method 2: If ARP table is empty or we need more info, try arp-scan
        if not devices:
            devices = self._scan_with_arp_scan()
        
        # Method 3: Fallback to nmap
        if not devices:
            devices = self._scan_with_nmap()
        
        # Enhance device information
        for device in devices:
            # Resolve hostname
            device["hostname"] = self._resolve_hostname(device["ip_address"])
            # Lookup manufacturer
            device["manufacturer"] = self._lookup_manufacturer(device["mac_address"])
            # Guess device type (basic heuristics)
            device["device_type"] = self._guess_device_type(device)
        
        logger.info(f"Scanned {len(devices)} devices on network")
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
        elif "amazon" in manufacturer:
            return "iot_device"
        elif "google" in manufacturer:
            return "iot_device"
        
        return "unknown"
