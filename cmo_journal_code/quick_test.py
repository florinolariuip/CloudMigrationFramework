#!/usr/bin/env python3
"""Quick test of pricing system without slow API calls"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_pricing_speed():
    print("Testing pricing system performance...")
    
    try:
        # Test fallback data (should be instant)
        from services.pricing import service_cache
        
        print("1. Testing fallback data...")
        fallback = service_cache.get_fallback_data()
        print(f"   Fallback services: {len(fallback['costs'])}")
        print(f"   Sample prices: AWS EC2=${fallback['costs']['AWS EC2']}, Azure VM=${fallback['costs']['Azure VM']}")
        
        # Test service cache with force refresh (will try APIs but timeout quickly)
        print("\n2. Testing service cache (with fast timeout)...")
        import time
        start = time.time()
        
        data = service_cache.get_service_data(force_refresh=True)
        
        elapsed = time.time() - start
        print(f"   Cache refresh took: {elapsed:.2f}s")
        print(f"   Total services: {len(data.get('costs', {}))}")
        print(f"   Live data %: {data.get('live_data_percentage', 0)}%")
        
        # Test individual service lookup
        print("\n3. Testing service lookup...")
        from services.pricing import get_cost_for_service
        
        services_to_test = ['AWS EC2', 'Azure VM', 'GCP Compute Engine']
        for service in services_to_test:
            start = time.time()
            cost = get_cost_for_service(service)
            elapsed = time.time() - start
            print(f"   {service}: ${cost:.2f} ({elapsed*1000:.1f}ms)")
        
        print("\n4. Performance summary:")
        if elapsed < 5:
            print("   GOOD: System responds in <5 seconds")
        elif elapsed < 10:
            print("   OK: System responds in <10 seconds") 
        else:
            print("   SLOW: System taking >10 seconds")
        
        return elapsed
    
    except Exception as e:
        print(f"Error during testing: {e}")
        print("This might be due to server connection issues - try the robust server instead.")
        return None

if __name__ == "__main__":
    result = test_pricing_speed()
    if result is None:
        print("\nTip: Use 'python robust_server.py' for better connection handling")