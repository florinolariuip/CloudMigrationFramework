#!/usr/bin/env python3
"""Test real Azure pricing API"""

import requests
import time

def test_azure_api():
    print("Testing Azure Retail Pricing API...")
    
    # Test Azure VM pricing
    url = "https://prices.azure.com/api/retail/prices"
    params = {
        "$filter": "serviceName eq 'Virtual Machines' and armRegionName eq 'westeurope' and skuName eq 'D2s v3' and contains(productName,'Linux')"
    }
    
    try:
        print("Calling Azure API...")
        start = time.time()
        resp = requests.get(url, params=params, timeout=10)
        elapsed = time.time() - start
        
        print(f"Response time: {elapsed:.2f}s")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            items = data.get('Items', [])
            print(f"Found {len(items)} pricing items")
            
            if items:
                item = items[0]
                price = float(item.get('retailPrice', 0))
                uom = item.get('unitOfMeasure', '')
                
                print(f"Azure VM D2s v3:")
                print(f"  Price: ${price:.4f} per {uom}")
                
                if 'hour' in uom.lower():
                    monthly = price * 730
                    print(f"  Monthly: ${monthly:.2f}")
                    return monthly
                else:
                    print(f"  Monthly: ${price:.2f}")
                    return price
            else:
                print("No pricing data found")
        else:
            print(f"API Error: {resp.text}")
            
    except Exception as e:
        print(f"Error: {e}")
    
    return None

def test_multiple_services():
    print("\nTesting multiple Azure services...")
    
    services = [
        ("Virtual Machines", "skuName eq 'D2s v3'", "Azure VM"),
        ("SQL Database", "contains(meterName,'Gen5') and contains(meterName,'2 vCore')", "Azure SQL"),
        ("Storage", "skuName eq 'Standard_LRS'", "Azure Storage")
    ]
    
    results = {}
    
    for service_name, filter_extra, display_name in services:
        print(f"\nTesting {display_name}...")
        
        url = "https://prices.azure.com/api/retail/prices"
        params = {
            "$filter": f"serviceName eq '{service_name}' and armRegionName eq 'westeurope' and {filter_extra}"
        }
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('Items', [])
                
                if items:
                    item = items[0]
                    price = float(item.get('retailPrice', 0))
                    uom = item.get('unitOfMeasure', '')
                    
                    if 'hour' in uom.lower():
                        monthly = price * 730
                    else:
                        monthly = price
                    
                    results[display_name] = monthly
                    print(f"  SUCCESS: ${monthly:.2f}/month")
                else:
                    print(f"  No data found")
            else:
                print(f"  API Error: {resp.status_code}")
                
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\nReal Azure Prices Retrieved:")
    for service, price in results.items():
        print(f"  {service}: ${price:.2f}/month")
    
    return results

if __name__ == "__main__":
    # Test single service first
    azure_vm_price = test_azure_api()
    
    # Test multiple services
    all_prices = test_multiple_services()
    
    if all_prices:
        print(f"\nSUCCESS: Retrieved {len(all_prices)} real prices from Azure API")
    else:
        print("\nFAILED: Could not retrieve real prices")