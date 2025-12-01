#!/usr/bin/env python3
"""Kill stuck processes and restart clean"""

import subprocess
import time

def kill_stuck_processes():
    print("Killing stuck processes...")
    
    # Kill processes on ports 5055 and 8080
    try:
        subprocess.run(["taskkill", "/F", "/IM", "python.exe"], capture_output=True)
        print("Killed Python processes")
    except:
        pass
    
    time.sleep(2)
    
    # Start fresh
    print("Starting fresh servers...")
    try:
        # Start backend
        backend = subprocess.Popen([
            "python", "-m", "flask", "--app", "backend.app:app", 
            "run", "--host", "127.0.0.1", "--port", "5055", "--no-reload"
        ])
        
        time.sleep(3)
        
        # Start frontend  
        frontend = subprocess.Popen([
            "python", "-m", "http.server", "8080", "--bind", "127.0.0.1"
        ], cwd="frontend")
        
        print("Servers restarted. Test with: python simple_test.py")
        
    except Exception as e:
        print(f"Restart failed: {e}")

if __name__ == "__main__":
    kill_stuck_processes()