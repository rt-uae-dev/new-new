#!/usr/bin/env python3
"""
Debug script to test main pipeline execution
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("🔍 Testing main pipeline imports...")

try:
    print("📦 Importing main_pipeline_refactored...")
    from main_pipeline_refactored import main
    print("✅ Successfully imported main function")
    
    print("🔍 Testing main function execution...")
    print("=" * 50)
    
    # Test the main function
    main()
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
