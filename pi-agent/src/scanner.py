"""Network scanner - supports both simulation and real scanning."""
import random
import string
from typing import List, Dict, Any


class NetworkScanner:
    def __init__(self, simulation_mode: bool = False):
        self.simulation_mode = simulation_mode
        self._simulated_devices = []
    
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
        Real network scanning (requires root/admin and scapy/nmap).
        
        For production, you would:
        1. Use scapy to sniff ARP packets
        2. Use nmap for active scanning
        3. Query manufacturer database for OUI lookup
        
        Example with scapy (requires sudo):
        ```
        from scapy.all import ARP, Ether, srp
        
        arp = ARP(pdst="192.168.1.0/24")
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether/arp
        result = srp(packet, timeout=3, verbose=0)[0]
        
        devices = []
        for sent, received in result:
            devices.append({
                "mac_address": received.hwsrc,
                "ip_address": received.psrc,
                "hostname": None,  # Resolve via socket.gethostbyaddr
                "manufacturer": None,  # Lookup via OUI database
                "device_type": "unknown"
            })
        return devices
        ```
        """
        print("Real scanning not implemented yet (requires root + scapy/nmap)")
        print("Enable simulation_mode in config.yaml for POC testing")
        return []
