#!/usr/bin/env python3
"""
MOHRE Document Processing Pipeline
Main Entry Point
"""

import sys
import os

# Set up Google Cloud credentials BEFORE importing any Google libraries
if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
    config_path = os.path.join(os.path.dirname(__file__), "config", "GOOGLEAPI.json")
    if os.path.exists(config_path):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.abspath(config_path)
        print(f"[INFO] Set GOOGLE_APPLICATION_CREDENTIALS to: {config_path}")

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main_pipeline_refactored import main

if __name__ == "__main__":
    main() 