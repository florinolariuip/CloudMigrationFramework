#!/usr/bin/env python3
"""Simple test without complex imports"""

import requests
import time

def test_basic_system():
    print("=== BASIC SYSTEM TEST ===")
    
    # Test 1: Backend connectivity
    print("1. Testing backend connectivity...")
    try:
        resp = requests.get("http://localhost:5055/api/version", timeout=3)
        if resp.status_code == 200:
            print("   [OK] Backend is running")
            print(f"   Response: {resp.json()}")
        else:
            print(f"   [ERROR] Backend returned {resp.status_code}")
    except requests.exceptions.ConnectionError:
        print("   [ERROR] Backend not running - start with 'python run.py'")
    except Exception as e:
        print(f"   [ERROR] Backend test failed: {e}")
    
    # Test 2: Simple optimization
    print("\n2. Testing simple optimization...")
    try:
        payload = {
            "constraints": {"maxBudget": 5000, "maxLatency": 150, "maxProviders": 2},
            "preferences": {"prioritizeCost": True}
        }
        resp = requests.post("http://localhost:5055/api/optimize", json=payload, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print("   [OK] Optimization works")
            print(f"   Found {len(data.get('results', []))} solutions")
        else:
            print(f"   [ERROR] Optimization failed: {resp.status_code}")
    except requests.exceptions.Timeout:
        print("   [ERROR] Optimization timed out (system may be stuck)")
    except Exception as e:
        print(f"   [ERROR] Optimization test failed: {e}")
    
    # Test 3: Check if baseline comparison is running
    print("\n3. Testing baseline comparison...")
    try:
        payload = {
            "constraints": {"maxBudget": 5000, "maxLatency": 150, "maxProviders": 2},
            "preferences": {"prioritizeCost": True},
            "runBaselines": True
        }
        start = time.time()
        resp = requests.post("http://localhost:5055/api/optimize", json=payload, timeout=5)
        elapsed = time.time() - start
        
        if resp.status_code == 200:
            print(f"   [OK] Baselines completed in {elapsed:.1f}s")
        else:
            print(f"   [ERROR] Baselines failed: {resp.status_code}")
    except requests.exceptions.Timeout:
        print("   [WARNING] Baselines timed out - this is the freezing issue")
    except Exception as e:
        print(f"   [ERROR] Baseline test failed: {e}")

if __name__ == "__main__":
    test_basic_system()