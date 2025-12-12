"""
Quick setup script for downloading models locally
Run this from the project root directory
"""
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from backend.download_models import main

if __name__ == "__main__":
    # Change to backend directory for relative paths
    os.chdir(Path(__file__).parent / "backend")
    main()

