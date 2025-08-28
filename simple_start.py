import os
import sys
import time
from datetime import datetime

print("\n" + "="*60)
print("  SIMPLE BOT STARTER")
print("="*60)

# Navigate to correct directory
os.chdir(r"C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2")
sys.path.insert(0, os.getcwd())

print("\nStarting bot...")

try:
    # Try to import and run
    from orchestrator import run
    run.main()
except Exception as e:
    print(f"Error: {e}")
    print("\nPress Enter to exit...")
    input()
