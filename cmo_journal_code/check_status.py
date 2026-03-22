#!/usr/bin/env python3
"""Quick status check of the system"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def check_system_status():
    print("Checking system status...")
    
    try:
        # Test if backend is responsive
        import requests
        resp = requests.get("http://localhost:5055/api/version", timeout=2)
        if resp.status_code == 200:
            print("[OK] Backend is running and responsive")
        else:
            print("[ERROR] Backend not responding properly")
    except:
        print("[ERROR] Backend not accessible")
    
    # Check if baseline is still running
    try:
        from services.pricing import service_cache
        data = service_cache.get_service_data()
        print(f"[OK] Cache has {len(data.get('costs', {}))} services")
        print(f"[OK] Live data: {data.get('live_data_percentage', 0)}%")
    except Exception as e:
        print(f"[ERROR] Cache issue: {e}")
    
    print("\nIf baselines are stuck, restart the application.")

if __name__ == "__main__":
    check_system_status()