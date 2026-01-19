
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Attempting to import app from server.py...")
    from server import app
    print("Import successful!")
    
    print("\nRegistered Routes:")
    for route in app.routes:
        print(f" - {route.path} [{route.name}]")
        
except Exception as e:
    print(f"FAILED to import app: {e}")
    import traceback
    traceback.print_exc()
