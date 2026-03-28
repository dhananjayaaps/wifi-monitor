"""Usage stats collector - monitors network traffic per device."""
import random
import subprocess
import re
import logging
import shutil
from typing import List, Dict, Any, Optional
from collections import defaultdict


logger = logging.getLogger(__name__)


class StatsCollector:
    def __init__(self, simulation_mode: bool = False, interface: str = "wlan0", hotspot_mode: bool = False,
                 min_bytes: int = 1024, max_bytes: int = 104857600, alert_probability: float = 0.3):
        self.simulation_mode = simulation_mode
        self.interface = interface
        self.hotspot_mode = hotspot_mode
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes
        self.alert_probability = alert_probability
        self._tracked_devices = set()  # Track which devices have iptables rules
        self._last_counters = {}  # Store last counter values for delta calculation
        self._warned_mac_destination = False
        self._warned_iw_unavailable = False
        self.iptables_cmd = self._detect_iptables_cmd()
        self.supports_mac_destination = self._detect_mac_destination_support()
    
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

        # Hotspot mode: prefer per-station counters from iw
        if self.hotspot_mode:
            stats = self._collect_from_iw(devices)
            if stats:
                logger.info(f"Collected stats for {len(stats)} devices (iw)")
                return stats
        
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

    def _collect_from_iw(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Collect per-device stats using iw station dump."""
        stats = []
        if not devices:
            return stats

        if not shutil.which("iw"):
            if not self._warned_iw_unavailable:
                logger.warning("iw not installed; falling back to iptables/proc")
                self._warned_iw_unavailable = True
            return stats

        try:
            result = subprocess.run(
                ["sudo", "iw", "dev", self.interface, "station", "dump"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return stats

            station_bytes = {}
            current_mac = None
            for line in result.stdout.split("\n"):
                match = re.match(r"^Station\s+([0-9A-Fa-f:]{17})\s+", line)
                if match:
                    current_mac = match.group(1).upper()
                    station_bytes[current_mac] = {"rx": 0, "tx": 0}
                    continue

                if current_mac:
                    rx_match = re.search(r"rx bytes:\s+(\d+)", line)
                    tx_match = re.search(r"tx bytes:\s+(\d+)", line)
                    if rx_match:
                        station_bytes[current_mac]["rx"] = int(rx_match.group(1))
                    if tx_match:
                        station_bytes[current_mac]["tx"] = int(tx_match.group(1))

            device_macs = {d["mac_address"].upper(): d for d in devices if d.get("mac_address")}
            for mac, values in station_bytes.items():
                if mac not in device_macs:
                    continue

                # iw counters are from the AP perspective:
                # rx = bytes received by AP (device uploaded), tx = bytes sent by AP (device downloaded)
                current_up = values.get("rx", 0)
                current_down = values.get("tx", 0)

                key_up = f"{mac}_iw_up"
                key_down = f"{mac}_iw_down"

                # Initialize counters on first sight to avoid sending totals.
                if key_up not in self._last_counters or key_down not in self._last_counters:
                    self._last_counters[key_up] = current_up
                    self._last_counters[key_down] = current_down
                    continue

                last_up = self._last_counters.get(key_up, 0)
                last_down = self._last_counters.get(key_down, 0)

                delta_up = max(0, current_up - last_up)
                delta_down = max(0, current_down - last_down)

                self._last_counters[key_up] = current_up
                self._last_counters[key_down] = current_down

                stats.append({
                    "mac_address": mac,
                    "bytes_uploaded": delta_up,
                    "bytes_downloaded": delta_down
                })

        except Exception as e:
            logger.error(f"Error collecting from iw: {e}")

        return stats

    def _detect_iptables_cmd(self) -> str:
        """Select iptables binary, preferring iptables-legacy if available."""
        if shutil.which("iptables-legacy"):
            return "iptables-legacy"
        return "iptables"

    def _detect_mac_destination_support(self) -> bool:
        """Check whether iptables supports --mac-destination (nf_tables does not)."""
        try:
            result = subprocess.run([self.iptables_cmd, "-V"], capture_output=True, text=True, timeout=5)
            version_info = (result.stdout or "") + (result.stderr or "")
            if "nf_tables" in version_info:
                return False
        except Exception:
            pass
        return True
    
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
                "sudo", self.iptables_cmd, "-A", "WIFI_MONITOR_OUT",
                "-m", "mac", "--mac-source", mac,
                "-j", "RETURN"
            ]
            subprocess.run(upload_rule, capture_output=True, check=True, timeout=5)
            
            # Add rules for download (to device) - FORWARD chain for bridged traffic
            if self.supports_mac_destination:
                download_rule = [
                    "sudo", self.iptables_cmd, "-A", "WIFI_MONITOR_IN",
                    "-m", "mac", "--mac-destination", mac,
                    "-j", "RETURN"
                ]
                subprocess.run(download_rule, capture_output=True, check=True, timeout=5)
            elif not self._warned_mac_destination:
                logger.warning("iptables backend does not support --mac-destination; using interface stats")
                self._warned_mac_destination = True
            
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
                ["sudo", self.iptables_cmd, "-L", "WIFI_MONITOR_OUT", "-n"],
                capture_output=True,
                timeout=5
            )
            
            if result.returncode != 0:
                # Create chains
                subprocess.run(["sudo", self.iptables_cmd, "-N", "WIFI_MONITOR_OUT"], 
                             capture_output=True, timeout=5)
                subprocess.run(["sudo", self.iptables_cmd, "-N", "WIFI_MONITOR_IN"], 
                             capture_output=True, timeout=5)
                
                # Insert jump rules to custom chains
                subprocess.run(["sudo", self.iptables_cmd, "-I", "FORWARD", "1", "-j", "WIFI_MONITOR_OUT"],
                             capture_output=True, timeout=5)
                subprocess.run(["sudo", self.iptables_cmd, "-I", "FORWARD", "1", "-j", "WIFI_MONITOR_IN"],
                             capture_output=True, timeout=5)
                
                logger.info("Created WIFI_MONITOR chains")
        except Exception as e:
            logger.error(f"Error ensuring chains exist: {e}")
    
    def _collect_from_iptables(self, devices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Read byte counters from iptables rules."""
        stats = []

        if not self.supports_mac_destination:
            return stats
        
        try:
            # Get rules with counters
            result = subprocess.run(
                ["sudo", self.iptables_cmd, "-L", "WIFI_MONITOR_OUT", "-n", "-v", "-x"],
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
                ["sudo", self.iptables_cmd, "-L", "WIFI_MONITOR_IN", "-n", "-v", "-x"],
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
                key_up = f"{mac}_up"
                key_down = f"{mac}_down"

                # Initialize counters on first sight to avoid sending totals.
                if key_up not in self._last_counters or key_down not in self._last_counters:
                    self._last_counters[key_up] = current_up
                    self._last_counters[key_down] = current_down
                    continue

                last_up = self._last_counters.get(key_up, 0)
                last_down = self._last_counters.get(key_down, 0)
                
                delta_up = max(0, current_up - last_up)
                delta_down = max(0, current_down - last_down)
                
                # Store current values for next delta
                self._last_counters[key_up] = current_up
                self._last_counters[key_down] = current_down
                
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
                            key_rx = "interface_rx"
                            key_tx = "interface_tx"

                            # Initialize counters on first read to avoid totals.
                            if key_rx not in self._last_counters or key_tx not in self._last_counters:
                                self._last_counters[key_rx] = rx_bytes
                                self._last_counters[key_tx] = tx_bytes
                                return stats

                            last_rx = self._last_counters.get(key_rx, 0)
                            last_tx = self._last_counters.get(key_tx, 0)
                            
                            delta_rx = max(0, rx_bytes - last_rx)
                            delta_tx = max(0, tx_bytes - last_tx)
                            
                            self._last_counters[key_rx] = rx_bytes
                            self._last_counters[key_tx] = tx_bytes
                            
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
            subprocess.run(["sudo", self.iptables_cmd, "-F", "WIFI_MONITOR_OUT"], 
                         capture_output=True, timeout=5)
            subprocess.run(["sudo", self.iptables_cmd, "-F", "WIFI_MONITOR_IN"], 
                         capture_output=True, timeout=5)
            
            # Remove jump rules
            subprocess.run(["sudo", self.iptables_cmd, "-D", "FORWARD", "-j", "WIFI_MONITOR_OUT"],
                         capture_output=True, timeout=5)
            subprocess.run(["sudo", self.iptables_cmd, "-D", "FORWARD", "-j", "WIFI_MONITOR_IN"],
                         capture_output=True, timeout=5)
            
            # Delete chains
            subprocess.run(["sudo", self.iptables_cmd, "-X", "WIFI_MONITOR_OUT"], 
                         capture_output=True, timeout=5)
            subprocess.run(["sudo", self.iptables_cmd, "-X", "WIFI_MONITOR_IN"], 
                         capture_output=True, timeout=5)
            
            logger.info("Cleaned up iptables rules")
        except Exception as e:
            logger.error(f"Error cleaning up iptables: {e}")
