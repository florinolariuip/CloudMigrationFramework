#!/usr/bin/env python3
"""Start both backend and frontend servers"""

import subprocess
import time
import webbrowser
import os

def start_servers():
    print("Starting Cloud Migration Optimizer...")
    
    # Start backend
    print("Starting backend on port 5055...")
    backend_cmd = ["python", "-m", "flask", "--app", "backend.app:app", "run", "--host", "127.0.0.1", "--port", "5055"]
    backend = subprocess.Popen(backend_cmd, cwd=os.getcwd(), stdout=None, stderr=None)
    
    # Wait for backend to start
    time.sleep(3)
    
    # Start frontend
    print("Starting frontend on port 8080...")
    frontend_cmd = ["python", "-m", "http.server", "8080", "--bind", "127.0.0.1"]
    frontend = subprocess.Popen(frontend_cmd, cwd="frontend", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait and open browser
    time.sleep(2)
    print("Opening browser...")
    webbrowser.open("http://localhost:8080")
    
    print("Both servers started. Press Ctrl+C to stop.")
    
    try:
        # Keep running
        backend.wait()
    except KeyboardInterrupt:
        print("\nStopping servers...")
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    start_servers()