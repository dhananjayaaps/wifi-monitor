"""Main agent loop - orchestrates scanning, collection, and sync."""
import time
import signal
import sys
import logging
from datetime import datetime
from typing import Optional
from .config import Config
from .client import BackendClient
from .scanner import NetworkScanner
from .collector import StatsCollector
from .ddos_detector import DdosDetector
from .logger import setup_logging, get_logger


class Agent:
    def __init__(self, config_path: str = "config.yaml"):
        self.config = Config(config_path)
        
        # Setup logging
        setup_logging(
            log_dir=self.config.log_dir,
            log_level=self.config.log_level
        )
        self.logger = get_logger(__name__)
        
        # Initialize components
        self.client = BackendClient(
            base_url=self.config.api_base_url
        )
        self.scanner = NetworkScanner(
            simulation_mode=self.config.simulation_mode,
            interface=self.config.interface,
            hotspot_mode=self.config.hotspot_mode
        )
        self.collector = StatsCollector(
            simulation_mode=self.config.simulation_mode,
            interface=self.config.interface,
            hotspot_mode=self.config.hotspot_mode,
            min_bytes=self.config.simulation_min_bytes,
            max_bytes=self.config.simulation_max_bytes
        )

        self.ddos_detector = DdosDetector(
            model_path=self.config.ddos_model_path,
            enabled=self.config.ddos_enabled
        )
        self.ddos_min_confidence = self.config.ddos_min_confidence
        self.ddos_alert_cooldown = self.config.ddos_alert_cooldown_seconds
        self._last_ddos_alert = {}
        
        self.devices = []
        self.last_scan = 0
        self.last_stats = 0
        self.running = False
        self.authenticated = False
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.stop()
    
    def start(self):
        """Start the agent main loop."""
        self.logger.info("=== Pi Agent Starting ===")
        self.logger.info(f"Mode: {'SIMULATION' if self.config.simulation_mode else 'REAL'}")
        self.logger.info(f"Interface: {self.config.interface}")
        self.logger.info(f"Backend: {self.config.api_base_url}")
        self.logger.info(f"Scan interval: {self.config.scan_interval}s")
        self.logger.info(f"Stats interval: {self.config.stats_interval}s")
        self.logger.info(f"Log level: {self.config.log_level}")
        if self.ddos_detector.enabled and not self.ddos_detector.is_ready():
            self.logger.warning("DDoS detector enabled but model failed to load")
        else:
            self.logger.info(f"DDoS detector: {'ENABLED' if self.ddos_detector.enabled else 'DISABLED'}")
        
        if not self.config.api_key and (not self.config.auth_email or not self.config.auth_password):
            self.logger.error("Authentication credentials not configured!")
            self.logger.error("Please set auth.api_key or auth.email/auth.password in config.yaml")
            return
        
        # Authenticate with retry logic
        if not self._authenticate_with_retry():
            self.logger.error("Failed to authenticate after multiple attempts")
            return
        
        self.running = True
        self.logger.info("Agent running. Press Ctrl+C to stop.\n")
        
        try:
            while self.running:
                current_time = time.time()
                
                # Check connection health periodically
                if not self.authenticated:
                    self.logger.warning("Lost authentication, attempting to re-authenticate...")
                    if not self._authenticate_with_retry():
                        self.logger.error("Re-authentication failed, stopping agent")
                        break
                
                # Device scanning
                if current_time - self.last_scan >= self.config.scan_interval:
                    try:
                        self._scan_devices()
                        self.last_scan = current_time
                    except Exception as e:
                        self.logger.error(f"Error during device scan: {e}", exc_info=True)
                
                # Stats collection
                if current_time - self.last_stats >= self.config.stats_interval:
                    if self.devices:
                        try:
                            self._collect_and_send_stats()
                            self.last_stats = current_time
                        except Exception as e:
                            self.logger.error(f"Error during stats collection: {e}", exc_info=True)
                
                time.sleep(1)
        
        except Exception as e:
            self.logger.critical(f"Fatal error in main loop: {e}", exc_info=True)
        finally:
            self.stop()
    
    def _authenticate_with_retry(self) -> bool:
        """Authenticate with backend with retry logic."""
        for attempt in range(1, self.config.retry_attempts + 1):
            try:
                # Test connectivity
                self.logger.info(f"Testing connectivity (attempt {attempt}/{self.config.retry_attempts})...")
                if not self.client.health_check():
                    self.logger.warning("Backend health check failed")
                    if attempt < self.config.retry_attempts:
                        time.sleep(self.config.retry_delay)
                        continue
                    return False
                
                self.logger.info("✓ Connected to backend")

                # Prefer configured API key (stable across restarts)
                if self.config.api_key:
                    self.client.set_api_key(self.config.api_key)
                    if self.client.ping():
                        self.logger.info("✓ Authenticated with API key")
                        self.authenticated = True
                        return True
                    self.logger.warning("API key ping failed; falling back to login")

                # Authenticate via email/password to obtain or reuse API key
                self.logger.info("Authenticating...")
                api_key = self.client.login(self.config.auth_email, self.config.auth_password)
                if not api_key:
                    self.logger.error("Authentication failed (invalid credentials)")
                    if attempt < self.config.retry_attempts:
                        time.sleep(self.config.retry_delay)
                        continue
                    return False

                self.logger.info("✓ Authenticated successfully")
                self.logger.info(f"✓ Obtained API key: {api_key[:20]}...")

                # Test agent authentication
                if not self.client.ping():
                    self.logger.error("Agent ping failed")
                    if attempt < self.config.retry_attempts:
                        time.sleep(self.config.retry_delay)
                        continue
                    return False

                self.logger.info("✓ Agent ready")
                self.authenticated = True
                return True
                
            except Exception as e:
                self.logger.error(f"Authentication attempt {attempt} failed: {e}")
                if attempt < self.config.retry_attempts:
                    time.sleep(self.config.retry_delay)
        
        return False
    
    def _scan_devices(self):
        """Scan network and sync devices."""
        self.logger.info("Scanning network...")
        
        device_count = self.config.simulation_device_count if self.config.simulation_mode else None
        devices = self.scanner.scan(device_count=device_count)
        
        if not devices:
            self.logger.warning("No devices found")
            return
        
        self.logger.info(f"Found {len(devices)} device(s)")
        
        # Sync with backend with retry
        result = self._sync_with_retry(devices)
        if result:
            self.logger.info(f"✓ Synced {result['data']['synced_count']} devices")
            self.devices = devices
        else:
            self.logger.error("Failed to sync devices after retries")
    
    def _sync_with_retry(self, devices):
        """Sync devices with retry logic."""
        for attempt in range(1, self.config.retry_attempts + 1):
            result = self.client.sync_devices(devices)
            if result:
                return result
            
            if attempt < self.config.retry_attempts:
                self.logger.warning(f"Sync failed, retrying in {self.config.retry_delay}s...")
                time.sleep(self.config.retry_delay)
        
        return None
    
    def _collect_and_send_stats(self):
        """Collect stats and send to backend."""
        self.logger.info("Collecting stats...")
        
        stats = self.collector.collect(self.devices)
        
        if not stats:
            self.logger.warning("No stats collected")
            return
        
        self.logger.info(f"Collected stats for {len(stats)} device(s)")
        
        # Send to backend with retry
        result = self._ingest_with_retry(stats)
        if result:
            self.logger.info(f"✓ Ingested {result['data']['ingested_count']} stats")
        else:
            self.logger.error("Failed to ingest stats after retries")

        # Run DDoS detection on collected stats
        if self.ddos_detector.enabled and self.ddos_detector.is_ready():
            self._detect_and_alert(stats)

    def _detect_and_alert(self, stats):
        """Detect DDoS/DOS patterns and send alerts."""
        devices_by_mac = {d.get("mac_address", "").upper(): d for d in self.devices}
        detections = self.ddos_detector.predict(stats, devices_by_mac, self.config.stats_interval)
        alerts = []
        now = time.time()

        for detection in detections:
            prediction = detection.prediction.lower()
            if prediction not in {"dos", "ddos"}:
                continue
            if detection.confidence < self.ddos_min_confidence:
                continue

            key = (detection.mac_address.upper(), prediction)
            last_sent = self._last_ddos_alert.get(key, 0)
            if now - last_sent < self.ddos_alert_cooldown:
                continue

            alerts.append({
                "mac_address": detection.mac_address,
                "alert_type": prediction,
                "confidence": detection.confidence,
                "total_bytes": detection.total_bytes,
            })
            self._last_ddos_alert[key] = now

        if not alerts:
            return

        result = self.client.ingest_detection_alerts(alerts)
        if result:
            self.logger.warning(f"✓ DDoS alerts sent: {result['data']['ingested_count']}")
        else:
            self.logger.error("Failed to send DDoS alerts")
    
    def _ingest_with_retry(self, stats):
        """Ingest stats with retry logic."""
        for attempt in range(1, self.config.retry_attempts + 1):
            result = self.client.ingest_stats(stats)
            if result:
                return result
            
            if attempt < self.config.retry_attempts:
                self.logger.warning(f"Ingestion failed, retrying in {self.config.retry_delay}s...")
                time.sleep(self.config.retry_delay)
        
        return None
    
    def stop(self):
        """Stop the agent and cleanup resources."""
        if not self.running:
            return
        
        self.logger.info("Stopping agent...")
        self.running = False
        
        # Cleanup iptables rules if using real collector
        if not self.config.simulation_mode:
            try:
                self.collector.cleanup()
            except Exception as e:
                self.logger.error(f"Error during collector cleanup: {e}")
        
        self.logger.info("Agent stopped")
        sys.exit(0)
