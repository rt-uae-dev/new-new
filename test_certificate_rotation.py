#!/usr/bin/env python3
"""
Test script to verify certificate rotation functionality
"""

import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_certificate_rotation():
    """Test certificate rotation with multiple certificate images"""
    
    # Test with multiple certificates from the dataset
    test_certificates = [
        "data/dataset/certificate/05.1DegreeCertificate_page_1_1_1_1.jpg",
        "data/dataset/certificate/03. Diploma In Mechanical with UAE Attestation_page_2_1.jpg",
        "data/dataset/certificate/Amit degree_page_1_1.jpg",
        "data/dataset/certificate/Attested Degree_page_1_1_1.jpg"
    ]
    
    for test_certificate in test_certificates:
        if not os.path.exists(test_certificate):
            print(f"❌ Test certificate not found: {test_certificate}")
            continue
        
        print(f"\n🔍 Testing certificate rotation with: {os.path.basename(test_certificate)}")
        
        try:
            from simple_text_orientation_detector import auto_rotate_image_simple
            
            # Test rotation
            result_path = auto_rotate_image_simple(test_certificate)
            
            if result_path != test_certificate:
                print(f"✅ Certificate was rotated: {os.path.basename(result_path)}")
            else:
                print(f"✅ Certificate did not need rotation")
                
        except Exception as e:
            print(f"❌ Error testing certificate rotation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_certificate_rotation()
