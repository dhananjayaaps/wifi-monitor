"""API client for communicating with the backend."""
import requests
from typing import List, Dict, Any, Optional


class BackendClient:
    def __init__(self, base_url: str, api_key: str = ""):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
        if api_key:
            self.session.headers.update({"X-Agent-API-Key": api_key})
    
    def login(self, email: str, password: str) -> Optional[str]:
        """Login to get JWT token, then register agent to get API key."""
        try:
            # Step 1: Login to get JWT token
            response = requests.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password},
                timeout=5
            )
            if response.status_code != 200:
                print(f"Login failed: {response.status_code} - {response.text}")
                return None
            
            jwt_token = response.json().get("access_token")
            if not jwt_token:
                print("No access token in login response")
                return None
            
            # Step 2: Register agent to get API key
            response = requests.post(
                f"{self.base_url}/agents/register",
                json={"name": "pi-agent"},
                headers={"Authorization": f"Bearer {jwt_token}"},
                timeout=5
            )
            if response.status_code != 201:
                print(f"Agent registration failed: {response.status_code} - {response.text}")
                return None
            
            api_key = response.json().get("data", {}).get("api_key")
            if api_key:
                self.api_key = api_key
                self.session.headers.update({"X-Agent-API-Key": api_key})
            
            return api_key
        except Exception as e:
            print(f"Login error: {e}")
            return None
    
    def health_check(self) -> bool:
        """Test backend connectivity (no auth required)."""
        try:
            response = requests.get(f"{self.base_url}/system/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def ping(self) -> bool:
        """Test agent authentication."""
        try:
            response = self.session.get(f"{self.base_url}/agents/ping")
            return response.status_code == 200
        except Exception as e:
            print(f"Agent ping failed: {e}")
            return False
    
    def sync_devices(self, devices: List[Dict[str, Any]]) -> Optional[Dict]:
        """Sync device list with backend."""
        try:
            response = self.session.post(
                f"{self.base_url}/agents/devices",
                json={"devices": devices}
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Device sync failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Device sync error: {e}")
            return None
    
    def ingest_stats(self, stats: List[Dict[str, Any]]) -> Optional[Dict]:
        """Send usage stats to backend."""
        try:
            response = self.session.post(
                f"{self.base_url}/agents/stats",
                json={"stats": stats}
            )
            if response.status_code == 201:
                return response.json()
            else:
                print(f"Stats ingestion failed: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Stats ingestion error: {e}")
            return None
