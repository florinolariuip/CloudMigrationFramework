#!/usr/bin/env python3
"""
Test script for live API pricing integration.
Verifies that external APIs are properly integrated.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from services.pricing import (
    fetch_live_price, 
    fetch_azure_live_price,
    service_cache
)

def test_live_apis():
    """Test live API integration for all providers"""
    print("Testing Live API Integration\n")
    
    # Test services
    test_services = [
        ('AWS EC2', 'us-east-1'),
        ('Azure VM', 'westeurope'), 
        ('GCP Compute Engine', 'us-central1'),
        ('Azure SQL', 'westeurope'),
        ('AWS RDS', 'us-east-1')
    ]
    
    results = {}
    
    for service, region in test_services:
        print(f"Testing {service} in {region}...")
        try:
            price = fetch_live_price(service, region)
            if price is not None:
                results[service] = {'price': price, 'status': '✅ Live API'}
                print(f"  ✅ ${price:.2f}/month")
            else:
                results[service] = {'price': None, 'status': '❌ API Failed'}
                print(f"  ❌ API call failed")
        except Exception as e:
            results[service] = {'price': None, 'status': f'❌ Error: {e}'}
            print(f"  ❌ Error: {e}")
        print()
    
    # Test Azure Retail API specifically
    print("Testing Azure Retail API directly...")
    try:
        azure_price = fetch_azure_live_price('Azure VM', 'westeurope')
        if azure_price:
            print(f"  ✅ Azure VM: ${azure_price:.2f}/month")
        else:
            print(f"  ❌ Azure API returned no data")
    except Exception as e:
        print(f"  ❌ Azure API error: {e}")
    
    # Test service cache integration
    print("\nTesting Service Cache Integration...")
    try:
        data = service_cache.get_service_data(force_refresh=True)
        
        live_services = data.get('live_data_percentage', 0)
        api_status = data.get('api_status', {})
        
        print(f"  Live data percentage: {live_services}%")
        print(f"  AWS API: {'✅' if api_status.get('aws') else '❌'}")
        print(f"  Azure API: {'✅' if api_status.get('azure') else '❌'}")
        print(f"  GCP API: {'✅' if api_status.get('gcp') else '❌'}")
        
        # Show sample prices
        costs = data.get('costs', {})
        print(f"\nSample Live Prices:")
        for service in ['AWS EC2', 'Azure VM', 'GCP Compute Engine']:
            if service in costs:
                print(f"  {service}: ${costs[service]:.2f}/month")
                
    except Exception as e:
        print(f"  ❌ Cache integration error: {e}")
    
    # Summary
    print(f"\nSummary:")
    live_count = sum(1 for r in results.values() if r['status'].startswith('✅'))
    total_count = len(results)
    success_rate = live_count / total_count * 100
    
    print(f"  Live API Success: {live_count}/{total_count} ({success_rate:.1f}%)")
    
    if success_rate >= 80:
        print("  Excellent API integration!")
    elif success_rate >= 50:
        print("  Partial API integration - some providers failing")
    else:
        print("  Poor API integration - mostly using fallback data")
    
    return results

if __name__ == "__main__":
    test_live_apis()