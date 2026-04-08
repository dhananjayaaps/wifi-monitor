"""Configuration loader for pi-agent."""
import yaml
from pathlib import Path
from typing import Dict, Any


class Config:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self):
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            self._config = yaml.safe_load(f) or {}
    
    def get(self, key: str, default=None):
        """Get config value by key (supports dot notation)."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    @property
    def api_base_url(self) -> str:
        return self.get("api_base_url", "http://localhost:5000/api/v1")
    
    @property
    def auth_email(self) -> str:
        return self.get("auth.email", "")
    
    @property
    def auth_password(self) -> str:
        return self.get("auth.password", "")

    @property
    def api_key(self) -> str:
        return self.get("auth.api_key", "")
    
    @property
    def simulation_mode(self) -> bool:
        return self.get("simulation_mode", False)
    
    @property
    def scan_interval(self) -> int:
        return self.get("scan_interval", 30)
    
    @property
    def stats_interval(self) -> int:
        return self.get("stats_interval", 30)
    
    @property
    def simulation_device_count(self) -> int:
        return self.get("simulation.device_count", 5)
    
    @property
    def simulation_min_bytes(self) -> int:
        return self.get("simulation.min_bytes", 1024)
    
    @property
    def simulation_max_bytes(self) -> int:
        return self.get("simulation.max_bytes", 104857600)
    
    @property
    def interface(self) -> str:
        return self.get("interface", "wlan0")
    
    @property
    def log_level(self) -> str:
        return self.get("log_level", "INFO")
    
    @property
    def log_dir(self) -> str:
        return self.get("log_dir", "logs")
    
    @property
    def retry_attempts(self) -> int:
        return self.get("retry_attempts", 3)
    
    @property
    def retry_delay(self) -> int:
        return self.get("retry_delay", 5)
    
    @property
    def hotspot_mode(self) -> bool:
        return self.get("hotspot_mode", False)
    
    @property
    def internet_interface(self) -> str:
        return self.get("internet_interface", "eth0")

    @property
    def ddos_enabled(self) -> bool:
        return self.get("ddos_detector.enabled", False)

    @property
    def ddos_model_path(self) -> str:
        return self.get("ddos_detector.model_path", "ddos_model.joblib")

    @property
    def ddos_min_confidence(self) -> float:
        return self.get("ddos_detector.min_confidence", 0.7)

    @property
    def ddos_alert_cooldown_seconds(self) -> int:
        return self.get("ddos_detector.alert_cooldown_seconds", 300)

    @property
    def audio_alerts_enabled(self) -> bool:
        return self.get("audio_alerts.enabled", False)

    @property
    def audio_alerts_engine(self) -> str:
        return self.get("audio_alerts.engine", "auto")

    @property
    def audio_alerts_volume(self) -> int:
        return self.get("audio_alerts.volume", 80)

    @property
    def audio_alerts_language(self) -> str:
        return self.get("audio_alerts.language", "en")

    @property
    def audio_alerts_cooldown(self) -> int:
        return self.get("audio_alerts.cooldown_seconds", 60)
