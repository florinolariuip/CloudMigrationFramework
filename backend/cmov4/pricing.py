"""
CMOv4 Pricing Module
- Reuses V3 cloud provider URIs and live pricing logic
- Supports user-supplied pricing overrides
"""
from typing import Dict, Any, Optional
from backend.services.pricing import ServiceDataCache

class PricingManager:
    def __init__(self, user_pricing: Optional[Dict[str, Any]] = None):
        self.user_pricing = user_pricing or {}
        self.cache = ServiceDataCache()

    def get_pricing(self) -> Dict[str, Any]:
        # If user provided pricing, use it and fill missing with live data
        live_pricing = self.cache.fetch_cloud_pricing_data()
        pricing = live_pricing.copy() if live_pricing else {}
        # Override with user-supplied prices
        for provider, services in self.user_pricing.items():
            if provider not in pricing:
                pricing[provider] = {}
            for service, price in services.items():
                pricing[provider][service] = price
        return pricing

    def get_price(self, provider: str, service: str) -> Optional[float]:
        pricing = self.get_pricing()
        return pricing.get(provider, {}).get(service)
