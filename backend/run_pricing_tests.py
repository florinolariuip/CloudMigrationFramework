#!/usr/bin/env python3
"""
Run pricing validation tests and generate report
"""
import unittest
import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_pricing_tests():
    """Run all pricing-related tests and generate report"""
    print("Running Pricing Validation Tests")
    print("=" * 50)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test modules
    try:
        from tests.test_pricing_validation import TestPricingValidation
        from tests.test_cache_update import TestCacheUpdate
        
        suite.addTests(loader.loadTestsFromTestCase(TestPricingValidation))
        suite.addTests(loader.loadTestsFromTestCase(TestCacheUpdate))
        
        print(f"Loaded {suite.countTestCases()} test cases")
        
    except ImportError as e:
        print(f"Failed to import test modules: {e}")
        return False
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(suite)
    
    # Generate summary report
    print("\n" + "=" * 50)
    print("Test Summary Report")
    print("=" * 50)
    print(f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tests Run: {result.testsRun}")
    print(f"Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failed: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('\\n')[-2]}")
    
    # Test live API connectivity
    print("\nLive API Connectivity Test")
    print("-" * 30)
    
    try:
        from services.pricing import service_cache
        data = service_cache.get_service_data(force_refresh=True)
        
        if "price_validation" in data:
            validation = data["price_validation"]
            print(f"Price Validation: {validation['validation_rate']}% passed")
            if validation["alerts"]:
                print(f"Price Alerts: {len(validation['alerts'])}")
        
        if "api_status" in data:
            api_status = data["api_status"]
            print(f"AWS API: {'OK' if api_status.get('aws') else 'FAIL'}")
            print(f"Azure API: {'OK' if api_status.get('azure') else 'FAIL'}")
            print(f"GCP API: {'OK' if api_status.get('gcp') else 'FAIL'}")
        
        print(f"Live Data: {data.get('live_data_percentage', 0)}%")
        
    except Exception as e:
        print(f"API connectivity test failed: {e}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall Result: {'PASS' if success else 'FAIL'}")
    
    return success

if __name__ == "__main__":
    success = run_pricing_tests()
    sys.exit(0 if success else 1)