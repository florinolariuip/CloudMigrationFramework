#!/usr/bin/env python3
"""Direct backend startup with visible logs"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    print("Starting backend with visible logs...")
    
    # Import and run Flask app directly
    from backend.app import app
    
    print("Backend starting on http://127.0.0.1:5055")
    print("You will see all pricing system logs here.")
    
    app.run(host='127.0.0.1', port=5055, debug=False)