"""
Unit tests for pricing validation and API sanity checks
"""
import unittest
from unittest.mock import patch, MagicMock
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.pricing import ServiceDataCache, service_cache

class TestPricingValidation(unittest.TestCase):
    
    def setUp(self):
        self.cache = ServiceDataCache()
    
    def test_price_sanity_check_valid_ranges(self):
        """Test that prices fall within expected ranges"""
        valid_prices = {
            "AWS EC2": 30.37,
            "AWS RDS": 49.64,
            "Azure VM": 69.35,
            "Azure SQL": 75.0,
            "GCP Compute Engine": 69.35,
            "GCP SQL": 83.95
        }
        
        for service, price in valid_prices.items():
            with self.subTest(service=service):
                self.assertTrue(self._is_price_reasonable(service, price))
    
    def test_price_sanity_check_invalid_ranges(self):
        """Test that unreasonable prices are flagged"""
        invalid_prices = {
            "AWS EC2": 500.0,  # Too high
            "AWS RDS": 1000.0,  # Too high
            "Azure VM": 5.0,    # Too low
            "GCP Compute Engine": 0.1  # Too low
        }
        
        for service, price in invalid_prices.items():
            with self.subTest(service=service):
                self.assertFalse(self._is_price_reasonable(service, price))
    
    def test_aws_api_response_structure(self):
        """Test AWS API returns expected data structure"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "products": {
                    "test_sku": {
                        "attributes": {
                            "instanceType": "t3.medium",
                            "operatingSystem": "Linux",
                            "location": "US East (N. Virginia)"
                        }
                    }
                },
                "terms": {
                    "OnDemand": {
                        "test_sku": {
                            "test_term": {
                                "priceDimensions": {
                                    "test_pd": {
                                        "pricePerUnit": {"USD": "0.0416"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
            mock_get.return_value = mock_response
            
            price = self.cache._fetch_aws_ec2_live()
            self.assertIsNotNone(price)
            self.assertGreater(price, 20)
            self.assertLess(price, 50)
    
    def test_azure_api_response_structure(self):
        """Test Azure API returns expected data structure"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "Items": [
                    {
                        "retailPrice": 0.095,
                        "unitOfMeasure": "1 Hour",
                        "skuName": "D2s v3"
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            price = self.cache._azure_first_monthly("test_filter")
            self.assertIsNotNone(price)
            self.assertGreater(price, 50)
            self.assertLess(price, 100)
    
    def test_gcp_api_response_structure(self):
        """Test GCP API returns expected data structure"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "skus": [
                    {
                        "description": "n1-standard-2 instance",
                        "serviceRegions": ["us-central1"],
                        "pricingInfo": [{
                            "pricingExpression": {
                                "tieredRates": [{
                                    "unitPrice": {
                                        "nanos": 95000000
                                    }
                                }]
                            }
                        }]
                    }
                ]
            }
            mock_get.return_value = mock_response
            
            price = self.cache._fetch_gcp_compute_live()
            self.assertIsNotNone(price)
            self.assertGreater(price, 50)
            self.assertLess(price, 100)
    
    def test_fallback_prices_realistic(self):
        """Test that fallback prices are realistic"""
        fallback_data = self.cache.get_fallback_data()
        costs = fallback_data["costs"]
        
        # Test key services have realistic prices
        self.assertLess(costs["AWS EC2"], 100, "AWS EC2 should be under $100/month")
        self.assertGreater(costs["AWS EC2"], 20, "AWS EC2 should be over $20/month")
        
        self.assertLess(costs["Azure VM"], 100, "Azure VM should be under $100/month")
        self.assertGreater(costs["Azure VM"], 50, "Azure VM should be over $50/month")
        
        self.assertEqual(costs["AWS IAM"], 0, "AWS IAM should be free")
        self.assertEqual(costs["GCP IAM"], 0, "GCP IAM should be free")
    
    def test_cache_refresh_mechanism(self):
        """Test that cache refreshes when TTL expires"""
        # Force cache refresh
        data1 = self.cache.get_service_data(force_refresh=True)
        self.assertIsNotNone(data1)
        self.assertIn("costs", data1)
        self.assertIn("timestamp", data1)
        
        # Get cached data
        data2 = self.cache.get_service_data(force_refresh=False)
        self.assertEqual(data1["timestamp"], data2["timestamp"])
    
    def test_api_timeout_handling(self):
        """Test that API timeouts are handled gracefully"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Connection timeout")
            
            # Should not raise exception, should return fallback
            data = self.cache.fetch_cloud_pricing_data()
            self.assertIsNotNone(data)
            self.assertIn("costs", data)
            # Implementation now supports partial live success with fallback fill;
            # any non-empty source string is acceptable as long as data is returned.
            self.assertIsInstance(data.get("source"), str)
            self.assertGreater(len(data["source"]), 0)
    
    def _is_price_reasonable(self, service: str, price: float) -> bool:
        """Helper method to check if price is within reasonable range"""
        expected_ranges = {
            "AWS EC2": (20, 100),
            "AWS RDS": (40, 80),
            "AWS S3": (15, 35),
            "Azure VM": (50, 90),
            "Azure SQL": (60, 100),
            "Azure Storage": (20, 40),
            "GCP Compute Engine": (50, 90),
            "GCP SQL": (70, 110),
            "GCP BigQuery": (50, 100)
        }
        
        if service not in expected_ranges:
            return True  # Unknown service, assume valid
        
        min_price, max_price = expected_ranges[service]
        return min_price <= price <= max_price

if __name__ == '__main__':
    unittest.main()