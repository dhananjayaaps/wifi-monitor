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
    def agent_api_key(self) -> str:
        return self.get("agent_api_key", "")
    
    @property
    def simulation_mode(self) -> bool:
        return self.get("simulation_mode", False)
    
    @property
    def scan_interval(self) -> int:
        return self.get("scan_interval", 30)
    
    @property
    def stats_interval(self) -> int:
        return self.get("stats_interval", 60)
    
    @property
    def simulation_device_count(self) -> int:
        return self.get("simulation.device_count", 5)
    
    @property
    def simulation_min_bytes(self) -> int:
        return self.get("simulation.min_bytes", 1024)
    
    @property
    def simulation_max_bytes(self) -> int:
        return self.get("simulation.max_bytes", 104857600)
