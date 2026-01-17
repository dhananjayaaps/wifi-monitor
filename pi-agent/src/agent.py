"""Main agent loop - orchestrates scanning, collection, and sync."""
import time
from datetime import datetime
from .config import Config
from .client import BackendClient
from .scanner import NetworkScanner
from .collector import StatsCollector


class Agent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        self.client = BackendClient(
            base_url=self.config.api_base_url
        )
        self.scanner = NetworkScanner(simulation_mode=self.config.simulation_mode)
        self.collector = StatsCollector(
            simulation_mode=self.config.simulation_mode,
            min_bytes=self.config.simulation_min_bytes,
            max_bytes=self.config.simulation_max_bytes
        )
        self.devices = []
        self.last_scan = 0
        self.last_stats = 0
    
    def start(self):
        """Start the agent main loop."""
        print(f"=== Pi Agent Starting ===")
        print(f"Mode: {'SIMULATION' if self.config.simulation_mode else 'REAL'}")
        print(f"Backend: {self.config.api_base_url}")
        print(f"Scan interval: {self.config.scan_interval}s")
        print(f"Stats interval: {self.config.stats_interval}s")
        
        if not self.config.auth_email or not self.config.auth_password:
            print("\n⚠️  ERROR: Authentication credentials not configured!")
            print("Please set auth.email and auth.password in config.yaml")
            return
        
        # Test connectivity
        print("\nTesting connectivity...")
        if not self.client.health_check():
            print("❌ Failed to connect to backend")
            return
        print("✓ Connected to backend")
        
        # Authenticate and get API key
        print("\nAuthenticating...")
        api_key = self.client.login(self.config.auth_email, self.config.auth_password)
        if not api_key:
            print("❌ Authentication failed (invalid credentials)")
            return
        print("✓ Authenticated successfully")
        print(f"✓ Obtained API key: {api_key[:20]}...")
        
        # Test agent authentication
        if not self.client.ping():
            print("❌ Agent ping failed")
            return
        print("✓ Agent ready")
        
        print("\nAgent running. Press Ctrl+C to stop.\n")
        
        try:
            while True:
                current_time = time.time()
                
                # Device scanning
                if current_time - self.last_scan >= self.config.scan_interval:
                    self._scan_devices()
                    self.last_scan = current_time
                
                # Stats collection
                if current_time - self.last_stats >= self.config.stats_interval:
                    if self.devices:
                        self._collect_and_send_stats()
                    self.last_stats = current_time
                
                time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\nAgent stopped by user")
    
    def _scan_devices(self):
        """Scan network and sync devices."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Scanning network...")
        
        device_count = self.config.simulation_device_count if self.config.simulation_mode else None
        devices = self.scanner.scan(device_count=device_count)
        
        if not devices:
            print("  No devices found")
            return
        
        print(f"  Found {len(devices)} device(s)")
        
        # Sync with backend
        result = self.client.sync_devices(devices)
        if result:
            print(f"  ✓ Synced {result['data']['synced_count']} devices")
            self.devices = devices
        else:
            print("  ❌ Failed to sync devices")
    
    def _collect_and_send_stats(self):
        """Collect stats and send to backend."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Collecting stats...")
        
        stats = self.collector.collect(self.devices)
        
        if not stats:
            print("  No stats collected")
            return
        
        print(f"  Collected stats for {len(stats)} device(s)")
        
        # Send to backend
        result = self.client.ingest_stats(stats)
        if result:
            print(f"  ✓ Ingested {result['data']['ingested_count']} stats")
        else:
            print("  ❌ Failed to ingest stats")
