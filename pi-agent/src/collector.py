"""Usage stats collector - monitors network traffic per device."""
import random
from typing import List, Dict, Any


class StatsCollector:
    def __init__(self, simulation_mode: bool = False, min_bytes: int = 1024, max_bytes: int = 104857600):
        self.simulation_mode = simulation_mode
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes
    
    def collect(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect usage stats for devices. Returns list of stat dicts."""
        if self.simulation_mode:
            return self._simulate_stats(devices)
        else:
            return self._real_collect(devices)
    
    def _simulate_stats(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fake stats for POC testing."""
        stats = []
        for device in devices:
            uploaded = random.randint(self.min_bytes, self.max_bytes)
            downloaded = random.randint(self.min_bytes, self.max_bytes)
            
            stats.append({
                "mac_address": device["mac_address"],
                "bytes_uploaded": uploaded,
                "bytes_downloaded": downloaded
            })
        
        return stats
    
    def _real_collect(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Real traffic collection (requires root and packet capture).
        
        For production, you would:
        1. Use scapy to capture packets
        2. Match packets to devices by MAC/IP
        3. Aggregate bytes sent/received per device
        
        Example with scapy (requires sudo):
        ```
        from scapy.all import sniff
        from collections import defaultdict
        
        stats = defaultdict(lambda: {"up": 0, "down": 0})
        
        def packet_handler(pkt):
            if pkt.haslayer('IP'):
                src_mac = pkt.src
                dst_mac = pkt.dst
                size = len(pkt)
                
                # Track upload (from device)
                stats[src_mac]["up"] += size
                # Track download (to device)
                stats[dst_mac]["down"] += size
        
        # Sniff for collection interval
        sniff(prn=packet_handler, timeout=60)
        
        result = []
        for mac, data in stats.items():
            result.append({
                "mac_address": mac,
                "bytes_uploaded": data["up"],
                "bytes_downloaded": data["down"]
            })
        return result
        ```
        """
        print("Real stats collection not implemented yet (requires root + scapy)")
        print("Enable simulation_mode in config.yaml for POC testing")
        return []
