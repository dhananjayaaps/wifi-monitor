"""Usage stats collector - monitors network traffic per device."""
import random
import subprocess
import re
import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict


logger = logging.getLogger(__name__)


class StatsCollector:
    def __init__(self, simulation_mode: bool = False, interface: str = "wlan0", 
                 min_bytes: int = 1024, max_bytes: int = 104857600, alert_probability: float = 0.3):
        self.simulation_mode = simulation_mode
        self.interface = interface
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes
        self.alert_probability = alert_probability
        self._tracked_devices = set()  # Track which devices have iptables rules
        self._last_counters = {}  # Store last counter values for delta calculation
    
    def collect(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect usage stats for devices. Returns list of stat dicts."""
        if self.simulation_mode:
            return self._simulate_stats(devices)
        else:
            return self._real_collect(devices)
    
    def _simulate_stats(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate fake stats for POC testing, with occasional high-usage spikes."""
        stats = []
        for device in devices:
            # Randomly simulate high-usage alerts (~30% of the time)
            if random.random() < self.alert_probability:
                # Simulate high usage that would trigger alerts
                uploaded = random.randint(int(self.max_bytes * 0.5), self.max_bytes)
                downloaded = random.randint(int(self.max_bytes * 0.5), self.max_bytes)
            else:
                # Normal usage
                uploaded = random.randint(self.min_bytes, int(self.max_bytes * 0.3))
                downloaded = random.randint(self.min_bytes, int(self.max_bytes * 0.3))
            
            stats.append({
                "mac_address": device["mac_address"],
                "bytes_uploaded": uploaded,
                "bytes_downloaded": downloaded
            })
        
        return stats
    
    def _real_collect(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Real traffic collection using iptables for per-device accounting.
        
        Uses iptables to count bytes per MAC address. Creates rules for new devices
        and reads counters for existing ones.
        """
        stats = []
        
        # Ensure iptables rules exist for all devices
        for device in devices:
            mac = device["mac_address"]
            if mac not in self._tracked_devices:
                if self._setup_iptables_rules(mac):
                    self._tracked_devices.add(mac)
        
        # Collect stats from iptables
        stats = self._collect_from_iptables(devices)
        
        # Fallback to /proc/net/dev if iptables fails
        if not stats:
            logger.warning("iptables collection failed, falling back to interface stats")
            stats = self._collect_from_proc(devices)
        
        logger.info(f"Collected stats for {len(stats)} devices")
        return stats
    
    def _setup_iptables_rules(self, mac: str) -> bool:
        """
        Create iptables accounting rules for a MAC address.
        
        Creates rules in INPUT/OUTPUT chains to count bytes for this device.
        Requires root/sudo access.
        """
        try:
            # Create custom chains if they don't exist
            self._ensure_chains_exist()
            
            # Add rules for upload (from device) - OUTPUT chain
            upload_rule = [
                "sudo", "iptables", "-A", "WIFI_MONITOR_OUT",
                "-m", "mac", "--mac-source", mac,
                "-j", "RETURN"
            ]
            subprocess.run(upload_rule, capture_output=True, check=True, timeout=5)
            
            # Add rules for download (to device) - FORWARD chain for bridged traffic
            download_rule = [
                "sudo", "iptables", "-A", "WIFI_MONITOR_IN",
                "-m", "mac", "--mac-destination", mac,
                "-j", "RETURN"
            ]
            subprocess.run(download_rule, capture_output=True, check=True, timeout=5)
            
            logger.info(f"Created iptables rules for device {mac}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create iptables rules for {mac}: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Error setting up iptables rules: {e}")
            return False
    
    def _ensure_chains_exist(self):
        """Create custom iptables chains for monitoring if they don't exist."""
        try:
            # Check if chains exist
            result = subprocess.run(
                ["sudo", "iptables", "-L", "WIFI_MONITOR_OUT", "-n"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # Create chains
                subprocess.run(["sudo", "iptables", "-N", "WIFI_MONITOR_OUT"], 
                             capture_output=True, timeout=5)
                subprocess.run(["sudo", "iptables", "-N", "WIFI_MONITOR_IN"], 
                             capture_output=True, timeout=5)
                
                # Insert jump rules to custom chains
                subprocess.run(["sudo", "iptables", "-I", "FORWARD", "1", "-j", "WIFI_MONITOR_OUT"],
                             capture_output=True, timeout=5)
                subprocess.run(["sudo", "iptables", "-I", "FORWARD", "1", "-j", "WIFI_MONITOR_IN"],
                             capture_output=True, timeout=5)
                
                logger.info("Created WIFI_MONITOR chains")
        except Exception as e:
            logger.error(f"Error ensuring chains exist: {e}")
    
    def _collect_from_iptables(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Read byte counters from iptables rules."""
        stats = []
        
        try:
            # Get rules with counters
            result = subprocess.run(
                ["sudo", "iptables", "-L", "WIFI_MONITOR_OUT", "-n", "-v", "-x"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return stats
            
            # Parse output to extract MAC -> bytes mapping
            upload_bytes = self._parse_iptables_output(result.stdout)
            
            # Get download stats
            result = subprocess.run(
                ["sudo", "iptables", "-L", "WIFI_MONITOR_IN", "-n", "-v", "-x"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            download_bytes = self._parse_iptables_output(result.stdout)
            
            # Combine stats for each device
            for device in devices:
                mac = device["mac_address"]
                
                # Get current counter values
                current_up = upload_bytes.get(mac, 0)
                current_down = download_bytes.get(mac, 0)
                
                # Calculate delta since last collection
                last_up = self._last_counters.get(f"{mac}_up", 0)
                last_down = self._last_counters.get(f"{mac}_down", 0)
                
                delta_up = max(0, current_up - last_up)
                delta_down = max(0, current_down - last_down)
                
                # Store current values for next delta
                self._last_counters[f"{mac}_up"] = current_up
                self._last_counters[f"{mac}_down"] = current_down
                
                stats.append({
                    "mac_address": mac,
                    "bytes_uploaded": delta_up,
                    "bytes_downloaded": delta_down
                })
            
        except Exception as e:
            logger.error(f"Error collecting from iptables: {e}")
        
        return stats
    
    def _parse_iptables_output(self, output: str) -> Dict[str, int]:
        """Parse iptables -L -v -x output to extract MAC -> bytes mapping."""
        mac_bytes = {}
        
        for line in output.split('\n'):
            # Look for lines with MAC addresses
            # Format: "  pkts bytes target  prot opt in out source destination"
            # Example: "  1234 567890 RETURN all -- * * 0.0.0.0/0 0.0.0.0/0 MAC 11:22:33:44:55:66"
            
            match = re.search(r'\s+\d+\s+(\d+).*MAC\s+([0-9A-Fa-f:]{17})', line)
            if match:
                bytes_count = int(match.group(1))
                mac = match.group(2).upper()
                mac_bytes[mac] = bytes_count
        
        return mac_bytes
    
    def _collect_from_proc(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback: Collect interface-level stats from /proc/net/dev.
        
        This won't give per-device stats, but provides overall interface usage.
        Distributes total bytes across all devices proportionally.
        """
        stats = []
        
        try:
            with open('/proc/net/dev', 'r') as f:
                lines = f.readlines()
                
                for line in lines:
                    if self.interface in line:
                        # Format: "interface: bytes packets ..."
                        parts = line.split()
                        if len(parts) >= 10:
                            # RX bytes (download) is field 1, TX bytes (upload) is field 9
                            rx_bytes = int(parts[1])
                            tx_bytes = int(parts[9])
                            
                            # Calculate delta
                            last_rx = self._last_counters.get('interface_rx', 0)
                            last_tx = self._last_counters.get('interface_tx', 0)
                            
                            delta_rx = max(0, rx_bytes - last_rx)
                            delta_tx = max(0, tx_bytes - last_tx)
                            
                            self._last_counters['interface_rx'] = rx_bytes
                            self._last_counters['interface_tx'] = tx_bytes
                            
                            # Distribute evenly across devices (not accurate, but better than nothing)
                            if devices:
                                rx_per_device = delta_rx // len(devices)
                                tx_per_device = delta_tx // len(devices)
                                
                                for device in devices:
                                    stats.append({
                                        "mac_address": device["mac_address"],
                                        "bytes_uploaded": tx_per_device,
                                        "bytes_downloaded": rx_per_device
                                    })
                            
                            break
            
            logger.info(f"Collected interface-level stats (distributed across {len(devices)} devices)")
            
        except Exception as e:
            logger.error(f"Error collecting from /proc/net/dev: {e}")
        
        return stats
    
    def cleanup(self):
        """Remove iptables rules on shutdown."""
        try:
            # Flush custom chains
            subprocess.run(["sudo", "iptables", "-F", "WIFI_MONITOR_OUT"], 
                         capture_output=True, timeout=5)
            subprocess.run(["sudo", "iptables", "-F", "WIFI_MONITOR_IN"], 
                         capture_output=True, timeout=5)
            
            # Remove jump rules
            subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-j", "WIFI_MONITOR_OUT"],
                         capture_output=True, timeout=5)
            subprocess.run(["sudo", "iptables", "-D", "FORWARD", "-j", "WIFI_MONITOR_IN"],
                         capture_output=True, timeout=5)
            
            # Delete chains
            subprocess.run(["sudo", "iptables", "-X", "WIFI_MONITOR_OUT"], 
                         capture_output=True, timeout=5)
            subprocess.run(["sudo", "iptables", "-X", "WIFI_MONITOR_IN"], 
                         capture_output=True, timeout=5)
            
            logger.info("Cleaned up iptables rules")
        except Exception as e:
            logger.error(f"Error cleaning up iptables: {e}")
