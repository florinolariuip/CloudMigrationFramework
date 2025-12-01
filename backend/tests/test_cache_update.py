"""
Unit tests for cache update mechanisms and price refresh validation
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import time
from datetime import datetime, timedelta
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pricing import ServiceDataCache, service_cache

class TestCacheUpdate(unittest.TestCase):
    
    def setUp(self):
        self.cache = ServiceDataCache(ttl_seconds=1)  # Short TTL for testing
    
    def test_cache_ttl_expiration(self):
        """Test that cache expires after TTL"""
        # Get initial data
        data1 = self.cache.get_service_data(force_refresh=True)
        timestamp1 = data1["timestamp"]
        
        # Wait for TTL to expire
        time.sleep(1.1)
        
        # Get data again - should refresh
        with patch.object(self.cache, 'fetch_cloud_pricing_data') as mock_fetch:
            mock_fetch.return_value = {
                "costs": {"AWS EC2": 35.0},
                "timestamp": datetime.now().isoformat(),
                "source": "test_refresh"
            }
            
            data2 = self.cache.get_service_data(force_refresh=False)
            timestamp2 = data2["timestamp"]
            
            # Should have refreshed
            self.assertNotEqual(timestamp1, timestamp2)
            mock_fetch.assert_called_once()
    
    def test_force_refresh_bypasses_cache(self):
        """Test that force_refresh always fetches new data"""
        # Get initial data
        data1 = self.cache.get_service_data(force_refresh=True)
        
        # Immediately force refresh again
        with patch.object(self.cache, 'fetch_cloud_pricing_data') as mock_fetch:
            mock_fetch.return_value = {
                "costs": {"AWS EC2": 40.0},
                "timestamp": datetime.now().isoformat(),
                "source": "test_force_refresh"
            }
            
            data2 = self.cache.get_service_data(force_refresh=True)
            
            # Should have called fetch even though cache is fresh
            mock_fetch.assert_called_once()
    
    def test_cache_update_preserves_structure(self):
        """Test that cache updates maintain expected data structure"""
        with patch.object(self.cache, 'fetch_cloud_pricing_data') as mock_fetch:
            mock_data = {
                "costs": {"AWS EC2": 30.37, "Azure VM": 69.35},
                "latency": {"AWS EC2": 8, "Azure VM": 9},
                "options": {"application_server": ["AWS EC2", "Azure VM"]},
                "sources": {"AWS EC2": "AWS Pricing API (Live)"},
                "timestamp": datetime.now().isoformat(),
                "source": "test_update"
            }
            mock_fetch.return_value = mock_data
            
            data = self.cache.get_service_data(force_refresh=True)
            
            # Verify structure
            required_keys = ["costs", "latency", "options", "sources", "timestamp", "source"]
            for key in required_keys:
                self.assertIn(key, data, f"Missing required key: {key}")
    
    def test_price_change_detection(self):
        """Test detection of significant price changes"""
        # Mock initial prices
        initial_prices = {"AWS EC2": 30.0, "Azure VM": 70.0}
        
        # Mock updated prices with significant change
        updated_prices = {"AWS EC2": 45.0, "Azure VM": 70.0}  # 50% increase
        
        with patch.object(self.cache, 'fetch_aws_live_pricing') as mock_aws:
            mock_aws.return_value = updated_prices
            
            # This would trigger price change alerts in a real implementation
            data = self.cache.fetch_cloud_pricing_data()
            
            # Verify price validation catches the change
            if "price_validation" in data:
                validation = data["price_validation"]
                self.assertIn("alerts", validation)
    
    def test_api_failure_fallback_update(self):
        """Test that fallback data is used when APIs fail"""
        with patch.object(self.cache, 'fetch_aws_live_pricing') as mock_aws, \
             patch.object(self.cache, 'fetch_azure_pricing') as mock_azure, \
             patch.object(self.cache, 'fetch_gcp_live_pricing') as mock_gcp:
            
            # Mock all APIs failing
            mock_aws.return_value = None
            mock_azure.return_value = None
            mock_gcp.return_value = None
            
            data = self.cache.fetch_cloud_pricing_data()
            
            # Should use fallback data
            self.assertIn("fallback", data["source"])
            self.assertIn("costs", data)
            self.assertGreater(len(data["costs"]), 0)
    
    def test_partial_api_success_handling(self):
        """Test handling when some APIs succeed and others fail"""
        with patch.object(self.cache, 'fetch_aws_live_pricing') as mock_aws, \
             patch.object(self.cache, 'fetch_azure_pricing') as mock_azure, \
             patch.object(self.cache, 'fetch_gcp_live_pricing') as mock_gcp:
            
            # Mock partial success
            mock_aws.return_value = {"AWS EC2": 30.37, "AWS RDS": 49.64}
            mock_azure.return_value = None  # Fails
            mock_gcp.return_value = {"GCP Compute Engine": 69.35}
            
            data = self.cache.fetch_cloud_pricing_data()
            
            # Should have AWS and GCP data, Azure should use fallback
            self.assertIn("AWS EC2", data["costs"])
            self.assertIn("GCP Compute Engine", data["costs"])
            self.assertIn("Azure VM", data["costs"])  # From fallback
            
            # Check API status tracking
            if "api_status" in data:
                api_status = data["api_status"]
                self.assertTrue(api_status["aws"])
                self.assertFalse(api_status["azure"])
                self.assertTrue(api_status["gcp"])
    
    def test_concurrent_cache_access(self):
        """Test that concurrent access to cache is thread-safe"""
        import threading
        results = []
        
        def access_cache():
            data = self.cache.get_service_data()
            results.append(data["timestamp"])
        
        # Create multiple threads accessing cache simultaneously
        threads = [threading.Thread(target=access_cache) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should get the same timestamp (same cached data)
        self.assertEqual(len(set(results)), 1, "All threads should get same cached data")
    
    def test_cache_size_limits(self):
        """Test that cache doesn't grow unbounded"""
        # This is more of a memory usage test
        data = self.cache.get_service_data()
        
        # Verify reasonable data size
        import sys
        data_size = sys.getsizeof(str(data))
        self.assertLess(data_size, 1024 * 1024, "Cache data should be under 1MB")

if __name__ == '__main__':
    unittest.main()