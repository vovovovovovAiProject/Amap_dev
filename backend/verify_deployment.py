import os
import sys
import requests
from pathlib import Path

print("--- Diagnostics ---")

# 1. Check Frontend Path
BASE_DIR = Path(".").resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
print(f"Frontend Dir: {FRONTEND_DIR}")
print(f"frontend exists: {FRONTEND_DIR.exists()}")

# 2. Check .env
ENV_FILE = Path(".env")
print(f".env exists: {ENV_FILE.exists()}")

# 3. Check Dependencies
try:
    import aiofiles
    print("aiofiles: Installed")
except ImportError:
    print("aiofiles: MISSING")

try:
    from fastapi.staticfiles import StaticFiles
    print("FastAPI StaticFiles: OK")
except ImportError:
    print("FastAPI StaticFiles: Error")

# 4. Check Server Response (Self)
try:
    r = requests.get("http://127.0.0.1:8000/", timeout=2)
    print(f"Root request status: {r.status_code}")
except Exception as e:
    print(f"Root request failed: {e}")

try:
    r = requests.get("http://127.0.0.1:8000/css/style.css", timeout=2)
    print(f"CSS request status: {r.status_code}")
except Exception as e:
    print(f"CSS request failed: {e}")
