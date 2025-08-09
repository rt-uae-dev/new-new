#!/usr/bin/env python3
"""
Simple Gemini 2.5 Flash orientation detector.
Just asks: "Does this image need to be rotated?"
"""

import os
import base64
import json
import google.generativeai as genai
import cv2
import pytesseract
from PIL import Image
import numpy as np

def simple_text_orientation_detection(image_path: str) -> dict:
    """
    Simple text-based orientation detection as fallback when Gemini API is not available.
    Uses OCR to detect text orientation and determines if rotation is needed.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        dict with rotation_needed (bool), rotation_angle (int), and reason (str)
    """
    try:
        # Read image
        image = cv2.imread(image_path)
        if image is None:
            return {
                'rotation_needed': False,
                'rotation_angle': 0,
                'reason': 'Could not read image'
            }
        
        # Convert to PIL Image for better OCR
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Try different rotations and get OCR confidence
        rotations = [0, 90, 180, 270]
        best_rotation = 0
        best_confidence = 0
        
        for rotation in rotations:
            # Rotate image
            if rotation == 0:
                rotated_image = pil_image
            elif rotation == 90:
                rotated_image = pil_image.rotate(90, expand=True)
            elif rotation == 180:
                rotated_image = pil_image.rotate(180, expand=True)
            elif rotation == 270:
                rotated_image = pil_image.rotate(270, expand=True)
            
            # Convert back to OpenCV format
            rotated_cv = cv2.cvtColor(np.array(rotated_image), cv2.COLOR_RGB2BGR)
            
            # Get OCR data
            try:
                ocr_data = pytesseract.image_to_data(rotated_cv, output_type=pytesseract.Output.DICT)
                
                # Calculate average confidence for text blocks
                confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
                    if avg_confidence > best_confidence:
                        best_confidence = avg_confidence
                        best_rotation = rotation
            except Exception as e:
                print(f"OCR error for rotation {rotation}: {e}")
                continue
        
        # Determine if rotation is needed
        if best_rotation == 0:
            return {
                'rotation_needed': False,
                'rotation_angle': 0,
                'reason': f'Simple text detection: Image is correctly oriented (confidence: {best_confidence:.1f})'
            }
        else:
            return {
                'rotation_needed': True,
                'rotation_angle': best_rotation,
                'reason': f'Simple text detection: Image needs {best_rotation}° rotation (confidence: {best_confidence:.1f})'
            }
            
    except Exception as e:
        print(f"❌ Error in simple text orientation detection: {e}")
        return {
            'rotation_needed': False,
            'rotation_angle': 0,
            'reason': f'Error occurred: {str(e)}'
        }

def ask_gemini_if_needs_rotation(image_path: str, is_passport_page: bool = False) -> dict:
    """
    Ask Gemini 2.5 Flash: "Does this image need to be rotated?"
    
    Args:
        image_path: Path to the image file
        is_passport_page: Whether this is a passport page (for enhanced prompts)
        
    Returns:
        dict with rotation_needed (bool), rotation_angle (int), and reason (str)
    """
    try:
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("⚠️ GEMINI_API_KEY not set, using fallback text-based orientation detection...")
            return simple_text_orientation_detection(image_path)
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 2.5 Flash
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_bytes = image_file.read()
        
        # Create the simple prompt with better instructions for all document types
        if is_passport_page:
            prompt = """
            Is this passport oriented properly? If not, how many degrees clockwise do I need to turn it?
            
            Answer with just a number:
            - 0 if it's already correct
            - 90 if you need to turn it 90 degrees clockwise
            - 180 if you need to turn it 180 degrees (upside down)
            - 270 if you need to turn it 270 degrees clockwise
            """
        else:
            prompt = """
            Look at this document image.
            
            SIMPLE RULES:
            - If the main text is at the TOP and readable = correct (reply 0)
            - If the main text is at the BOTTOM = upside down (reply 180)
            - If the main text is on the LEFT side = sideways (reply 90)
            - If the main text is on the RIGHT side = sideways (reply 270)
            
            Just tell me: 0, 90, 180, or 270
            """
        
        # Generate response from Gemini
        response = model.generate_content([prompt, {"mime_type": "image/jpeg", "data": image_bytes}])
        
        # Extract the response and determine rotation
        response_text = response.text.strip().lower()
        
        if is_passport_page:
            # For passports, extract the rotation angle directly from the response
            try:
                rotation_angle = int(response_text.strip())
                if rotation_angle not in [0, 90, 180, 270]:
                    rotation_angle = 0  # Default to no rotation if invalid response
            except ValueError:
                rotation_angle = 0  # Default to no rotation if can't parse
            
            rotation_needed = rotation_angle != 0
            if rotation_angle == 0:
                reason = "Gemini 2.5 Flash detected: Passport is correctly oriented"
            else:
                reason = f"Gemini 2.5 Flash detected: Passport needs {rotation_angle}° clockwise rotation"
        else:
            # For other documents, try to extract angle (fallback to text-based detection)
            try:
                rotation_angle = int(response_text)
                if rotation_angle not in [0, 90, 180, 270]:
                    rotation_angle = 0
            except ValueError:
                rotation_angle = 0
            
            rotation_needed = rotation_angle != 0
            if rotation_angle == 0:
                reason = "Gemini 2.5 Flash detected: Image is correctly oriented"
            else:
                reason = f"Gemini 2.5 Flash detected: Image needs {rotation_angle}° rotation"
        
        print(f"🤖 Gemini 2.5 Flash says: {response_text}")
        print(f"   Rotation needed: {rotation_needed}, Angle: {rotation_angle}°")
        
        return {
            'rotation_needed': rotation_needed,
            'rotation_angle': rotation_angle,
            'reason': reason
        }
                
    except Exception as e:
        print(f"❌ Error in Gemini 2.5 Flash orientation detection: {e}")
        print("⚠️ Falling back to simple text-based orientation detection...")
        return simple_text_orientation_detection(image_path)

def rotate_if_needed(image_path: str, is_passport_page: bool = False) -> str:
    """
    Ask Gemini 2.5 Flash if image needs rotation and rotate if needed.
    Includes verification step to ensure rotation was correct.
    
    Args:
        image_path: Path to the image file
        is_passport_page: Whether this is a passport page (for enhanced prompts)
        
    Returns:
        Path to the corrected image (original if no rotation needed)
    """
    print(f"🔍 Asking Gemini 2.5 Flash: Does this image need rotation?")
    print(f"   Image: {os.path.basename(image_path)}")
    
    # Ask Gemini 2.5 Flash
    result = ask_gemini_if_needs_rotation(image_path, is_passport_page=is_passport_page)
    
    print(f"📊 Gemini 2.5 Flash says:")
    print(f"   Rotation needed: {result['rotation_needed']}")
    print(f"   Reason: {result['reason']}")
    
    # Rotate if needed
    if result['rotation_needed']:
        print(f"🔄 Rotating image by {result['rotation_angle']}°...")
        
        # Read and rotate image
        image = cv2.imread(image_path)
        
        # Apply the correct rotation
        # When Gemini says "X° rotation needed", it means the image needs X° rotation to be correct
        # So we apply that exact rotation to fix it
        if result['rotation_angle'] == 90:
            print(f"   ↻ Rotating 90° clockwise to correct orientation")
            rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif result['rotation_angle'] == 180:
            print(f"   ↻ Rotating 180° to correct orientation")
            rotated_image = cv2.rotate(image, cv2.ROTATE_180)
        elif result['rotation_angle'] == 270:
            print(f"   ↺ Rotating 90° counterclockwise to correct orientation")
            rotated_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            print(f"❌ Invalid rotation angle: {result['rotation_angle']}")
            return image_path
        
        # Save rotated image by replacing the original file
        cv2.imwrite(image_path, rotated_image)
        print(f"✅ Rotated image saved by replacing original: {os.path.basename(image_path)}")
        
        # 🔄 VERIFICATION STEP: Ask Gemini again to verify the rotation was correct
        print(f"🔄 Verifying rotation was correct...")
        verification_result = ask_gemini_if_needs_rotation(image_path, is_passport_page=is_passport_page)
        
        if verification_result['rotation_needed']:
            print(f"⚠️ Gemini says rotation is still needed! Trying opposite rotation...")
            
            # If Gemini says it still needs rotation, try the opposite direction
            if result['rotation_angle'] == 90:
                print(f"   ↺ Trying 90° counterclockwise instead...")
                corrected_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            elif result['rotation_angle'] == 270:
                print(f"   ↻ Trying 90° clockwise instead...")
                corrected_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            elif result['rotation_angle'] == 180:
                print(f"   ↻ Trying 180° again (might be the same)...")
                corrected_image = cv2.rotate(image, cv2.ROTATE_180)
            else:
                print(f"❌ Unknown rotation angle, keeping original")
                return image_path
            
            # Save corrected image by replacing the original file
            cv2.imwrite(image_path, corrected_image)
            print(f"✅ Corrected image saved by replacing original: {os.path.basename(image_path)}")
            
            # Final verification
            final_verification = ask_gemini_if_needs_rotation(image_path, is_passport_page=is_passport_page)
            if not final_verification['rotation_needed']:
                print(f"✅ Final verification successful - rotation is now correct!")
                return image_path
            else:
                print(f"⚠️ Still not correct, keeping original image")
                return image_path
        else:
            print(f"✅ Verification successful - rotation was correct!")
            return image_path
    else:
        print(f"✅ No rotation needed - keeping original image")
        return image_path

def rotate_multi_page_documents(classified_images: list) -> None:
    """
    Enhanced rotation for multi-page documents, especially passports.
    Ensures that passport_1 (main page) is the reference for orientation,
    and passport_2 is rotated to match if needed.
    
    Args:
        classified_images: List of classified image data dictionaries
    """
    print("🔄 Enhanced multi-page document rotation...")
    
    # Group images by document type
    passport_1_images = [img for img in classified_images if img["label"] == "passport_1"]
    passport_2_images = [img for img in classified_images if img["label"] == "passport_2"]
    
    # First, ensure passport_1 pages are correctly oriented
    for img_data in passport_1_images:
        print(f"🔍 Checking primary passport page: {img_data['filename']}")
        rotated_path = rotate_if_needed(img_data["path"], is_passport_page=True)
        if rotated_path != img_data["path"]:
            img_data["rotated_path"] = rotated_path
            print(f"✅ Primary passport page rotated: {img_data['filename']}")
    
    # Then, check passport_2 pages and ensure they match the orientation of passport_1
    if passport_1_images and passport_2_images:
        print(f"🔍 Checking secondary passport pages to match primary orientation...")
        
        for img_data in passport_2_images:
            print(f"🔍 Checking secondary passport page: {img_data['filename']}")
            
            # Check if this page needs rotation using passport-specific prompt
            result = ask_gemini_if_needs_rotation(img_data["path"], is_passport_page=True)
            
            if result['rotation_needed']:
                print(f"🔄 Secondary passport page needs rotation: {result['rotation_angle']}°")
                
                # Read and rotate image
                image = cv2.imread(img_data["path"])
                
                # Apply rotation
                if result['rotation_angle'] == 90:
                    rotated_image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                elif result['rotation_angle'] == 180:
                    rotated_image = cv2.rotate(image, cv2.ROTATE_180)
                elif result['rotation_angle'] == 270:
                    rotated_image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                else:
                    continue
                
                # Save rotated image by replacing the original file
                cv2.imwrite(img_data["path"], rotated_image)
                img_data["rotated_path"] = img_data["path"]
                print(f"✅ Rotated image saved by replacing original: {img_data['filename']}")
                print(f"✅ Secondary passport page rotated: {img_data['filename']}")
            else:
                print(f"✅ Secondary passport page already correctly oriented: {img_data['filename']}")

if __name__ == "__main__":
    # Test with a sample image
    test_image = "data/dataset/passport_1/01. Passport Copy _Unaise_page_1_1_1_1.jpg"
    
    if os.path.exists(test_image):
        print(f"🧪 Testing Gemini 2.5 Flash orientation detection...")
        result = rotate_if_needed(test_image)
        print(f"Final result: {result}")
    else:
        print(f"Test image not found: {test_image}")
