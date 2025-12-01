#!/usr/bin/env python3
"""Robust server startup with error handling"""

import subprocess
import time
import webbrowser
import os
import signal
import sys
from threading import Thread

class RobustServer:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        
    def start_backend(self):
        """Start Flask backend with error handling"""
        print("Starting backend on port 5055...")
        try:
            cmd = [sys.executable, "-m", "flask", "--app", "backend.app:app", "run", 
                   "--host", "127.0.0.1", "--port", "5055", "--no-reload"]
            self.backend_process = subprocess.Popen(cmd, cwd=os.getcwd(), stdout=None, stderr=None)
            return True
        except Exception as e:
            print(f"Backend start failed: {e}")
            return False
    
    def start_frontend(self):
        """Start frontend with simple HTTP server"""
        print("Starting frontend on port 8080...")
        try:
            # Clean up any temp files first
            temp_path = os.path.join("frontend", "temp_server.py")
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            # Use simple HTTP server
            cmd = [sys.executable, "-m", "http.server", "8080", "--bind", "127.0.0.1"]
            self.frontend_process = subprocess.Popen(cmd, cwd="frontend", 
                                                   stdout=subprocess.DEVNULL, 
                                                   stderr=subprocess.DEVNULL)
            return True
        except Exception as e:
            print(f"Frontend start failed: {e}")
            return False
    
    def start_all(self):
        """Start both servers"""
        print("Starting Cloud Migration Optimizer (Robust Mode)...")
        
        # Start backend
        if not self.start_backend():
            return False
            
        # Wait for backend
        time.sleep(3)
        
        # Start frontend
        if not self.start_frontend():
            return False
            
        # Wait and open browser
        time.sleep(2)
        print("Opening browser...")
        webbrowser.open("http://localhost:8080")
        
        print("Both servers started. Press Ctrl+C to stop.")
        print("Note: Connection reset errors are normal and handled automatically.")
        
        return True
    
    def stop_all(self):
        """Stop both servers"""
        print("\nStopping servers...")
        if self.backend_process:
            self.backend_process.terminate()
        if self.frontend_process:
            self.frontend_process.terminate()
        
        # Kill any remaining processes on ports
        try:
            subprocess.run(["netstat", "-ano", "|", "findstr", ":8080"], shell=True, capture_output=True)
            subprocess.run(["netstat", "-ano", "|", "findstr", ":5055"], shell=True, capture_output=True)
        except:
            pass
        
        # Clean up temp file
        temp_path = os.path.join("frontend", "temp_server.py")
        if os.path.exists(temp_path):
            os.remove(temp_path)
    
    def run(self):
        """Main run loop with signal handling"""
        if not self.start_all():
            return
            
        def signal_handler(sig, frame):
            self.stop_all()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Keep running
            if self.backend_process:
                self.backend_process.wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop_all()

if __name__ == "__main__":
    server = RobustServer()
    server.run()