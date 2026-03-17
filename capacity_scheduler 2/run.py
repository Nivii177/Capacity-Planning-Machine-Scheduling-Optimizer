#!/usr/bin/env python3
"""
Quick start: python run.py
Opens http://localhost:5050 automatically.
"""
import subprocess
import sys
import os
import webbrowser
import time
import threading

def open_browser():
    time.sleep(1.5)
    webbrowser.open("http://localhost:5050")

if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Try to install deps silently
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "backend/requirements.txt", "-q"])
    except:
        pass

    threading.Thread(target=open_browser, daemon=True).start()
    
    print("\n🚀 SD Capacity Scheduler starting...")
    print("   → http://localhost:5050\n")
    
    from backend.app import app
    app.run(debug=False, port=5050, host="0.0.0.0")
