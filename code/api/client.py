import json
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging

# Handle imports differently based on how the module is being run
if __package__ is None or __package__ == '':
    # Running as a script
    from config import settings
else:
    # Running as a module
    from code.config import settings

logger = logging.getLogger(__name__)

class DealScoutAPI:
    """Client for interacting with the DealScout API."""
    
    def __init__(self, api_key: str = None, base_url: str = None):
        """Initialize the API client.
        
        Args:
            api_key: API key for authentication. If not provided, uses the one from settings.
            base_url: Base URL of the API. If not provided, uses the one from settings.
        """
        self.api_key = api_key or settings.API_KEY
        self.base_url = base_url or settings.API_BASE_URL
        self.session = self._create_session()
        self.cache: Dict[str, tuple[Any, float]] = {}
    
    def _create_session(self) -> requests.Session:
        """Create and configure a requests session with retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        
        # Mount the retry adapter
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        return session
    
    def _get_cached(self, key: str) -> Optional[Any]:
        """Get a value from the cache if it exists and hasn't expired."""
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < settings.CACHE_TTL:
                return value
            del self.cache[key]
        return None
    
    def _set_cache(self, key: str, value: Any) -> None:
        """Set a value in the cache."""
        self.cache[key] = (value, time.time())
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Make an API request with error handling and logging."""
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.warning(f"API request failed: {e}")
            # Return None to trigger fallback to mock data
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            return None
    
    def get_todays_deals(self, zip_code: str, radius: int, store_chains: List[str] = None) -> List[Dict]:
        """Get today's deals for the specified location and stores."""
        cache_key = f"deals_{zip_code}_{radius}_{'_'.join(sorted(store_chains or []))}"
        if cached := self._get_cached(cache_key):
            return cached
            
        params = {
            "zip_code": zip_code,
            "radius": radius,
        }
        if store_chains:
            params["chains"] = ",".join(store_chains)
            
        data = self._request("GET", "deals/today", params=params)
        self._set_cache(cache_key, data)
        return data
    
    def search_products(self, query: str, zip_code: str, radius: int) -> List[Dict]:
        """Search for products across stores."""
        cache_key = f"search_{query}_{zip_code}_{radius}"
        if cached := self._get_cached(cache_key):
            return cached
            
        params = {
            "query": query,
            "zip_code": zip_code,
            "radius": radius,
        }
        
        data = self._request("GET", "products/search", params=params)
        self._set_cache(cache_key, data)
        return data
    
    def get_nearby_stores(self, zip_code: str, radius: int, chains: List[str] = None) -> List[Dict]:
        """Get stores near the specified location."""
        cache_key = f"stores_{zip_code}_{radius}_{'_'.join(sorted(chains or []))}"
        if cached := self._get_cached(cache_key):
            return cached
            
        params = {
            "zip_code": zip_code,
            "radius": radius,
        }
        if chains:
            params["chains"] = ",".join(chains)
            
        data = self._request("GET", "stores/nearby", params=params)
        self._set_cache(cache_key, data)
        return data
    
    def get_store_details(self, store_id: str) -> Dict:
        """Get detailed information about a specific store."""
        cache_key = f"store_{store_id}"
        if cached := self._get_cached(cache_key):
            return cached
            
        data = self._request("GET", f"stores/{store_id}")
        self._set_cache(cache_key, data)
        return data
    
    def create_price_alert(self, product_id: str, target_price: float) -> Dict:
        """Create a price alert for a product."""
        data = {
            "product_id": product_id,
            "target_price": target_price,
        }
        return self._request("POST", "alerts", json=data)
    
    def get_user_alerts(self) -> List[Dict]:
        """Get the current user's price alerts."""
        return self._request("GET", "alerts")
    
    def delete_alert(self, alert_id: str) -> bool:
        """Delete a price alert."""
        self._request("DELETE", f"alerts/{alert_id}")
        return True
