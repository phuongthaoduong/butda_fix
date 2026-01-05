#!/usr/bin/env python3
"""
Startup script with error handling for debugging deployment issues.
"""
import sys
import os

print("="*60)
print("Starting Being-Up-To-Date Assistant Server")
print("="*60)
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")
print(f"Current directory: {os.getcwd()}")
print(f"PORT environment variable: {os.getenv('PORT', 'NOT SET')}")
print("="*60)

try:
    print("\n[1/4] Checking environment variables...")
    port = int(os.getenv("PORT", 8001))
    print(f"✓ Port: {port}")
    
    print("\n[2/4] Importing dependencies...")
    import fastapi
    print(f"✓ FastAPI: {fastapi.__version__}")
    
    import uvicorn
    print("✓ Uvicorn imported")
    
    print("\n[3/4] Importing application...")
    from main import app
    print("✓ Application imported successfully")
    
    print("\n[4/4] Starting server...")
    print(f"Listening on http://0.0.0.0:{port}")
    print("="*60 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
        timeout_keep_alive=120
    )
    
except ImportError as e:
    print(f"\n❌ IMPORT ERROR: {e}")
    print(f"Missing dependency: {e.name if hasattr(e, 'name') else 'unknown'}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
except Exception as e:
    print(f"\n❌ STARTUP ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

