#!/usr/bin/env python3
"""
Test Document AI extraction on Yogeshkumar's residence visa document
"""

import os
import sys
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# Set up environment variables
# Expect credentials in environment; do not hard-code in tests

from document_ai_processor import DOCUMENT_AI_PROCESSOR

def test_yogeshkumar_residence_visa():
    """Test Document AI extraction on Yogeshkumar's residence visa document"""
    
    # Path to the processed image
    image_path = "data/processed/COMPLETED/Fwd For Visa Cancellation Yogeshkumar Sant/YOGESHKUMAR_visa.jpg"
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"🔍 Testing Document AI on: {image_path}")
    print("=" * 60)
    
    # Process with Document AI
    result = DOCUMENT_AI_PROCESSOR.process_document(image_path)
    
    if "error" in result:
        print(f"❌ Document AI error: {result['error']}")
        return
    
    print(f"✅ Document AI processing successful!")
    print(f"📋 Document Type: {result.get('document_type', 'unknown')}")
    print(f"🎯 Confidence: {result.get('confidence', 0.0):.2f}")
    print(f"📝 Full Text Length: {len(result.get('full_text', ''))}")
    
    # Extract specific fields
    fields = DOCUMENT_AI_PROCESSOR.extract_specific_fields(result.get('full_text', ''))
    
    print(f"\n📋 Extracted Fields: {len(fields)}")
    for key, value in fields.items():
        print(f"   - {key}: {value}")
    
    # Check for file number patterns
    ocr_text = result.get('full_text', '')
    print(f"\n🔍 Looking for file number patterns in OCR text:")
    print("=" * 60)
    
    import re
    
    # Look for XXX/YYYY/ZZZZZZZ pattern
    file_patterns = [
        r'(\d{3}/\d{4}/\d{6,7})',  # 101/2019/3892898
        r'(\d{3}/\d{4}/\d{7})',   # 101/2019/3892898
        r'File\s*No[:\s]*([0-9/\s]+)',
        r'Identity\s*No[:\s]*([0-9/\s]+)',
        r'رقم\s*الهوية[:\s]*([0-9/\s]+)',
    ]
    
    for pattern in file_patterns:
        matches = re.findall(pattern, ocr_text, re.IGNORECASE)
        if matches:
            print(f"✅ Pattern '{pattern}' found: {matches}")
        else:
            print(f"❌ Pattern '{pattern}' not found")
    
    # Show a sample of the OCR text
    print(f"\n📄 Sample OCR Text (first 500 characters):")
    print("=" * 60)
    print(ocr_text[:500])
    print("...")

if __name__ == "__main__":
    test_yogeshkumar_residence_visa()
