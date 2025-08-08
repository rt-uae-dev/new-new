#!/usr/bin/env python3
"""
Google AI-based image rotation using Gemini Vision API.
Detects orientation and rotates images for passport pages, personal photos, and certificates.
"""

import cv2
import numpy as np
import os
import base64
import google.generativeai as genai
from PIL import Image
import io

# Configure Google Gemini API
import os
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Only rotate these document types
ROTATABLE_CLASSES = {"passport_1", "passport_2", "personal_photo", "certificate"}

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image to base64 string for Gemini Vision API.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"❌ Error encoding image to base64: {e}")
        return None

def detect_orientation_with_gemini(image_path: str, doc_class: str) -> dict:
    """
    Use Gemini Vision to detect if image needs rotation.
    Returns dict with rotation_needed (bool) and rotation_angle (int).
    """
    try:
        # Encode image to base64
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return {"rotation_needed": False, "rotation_angle": 0, "error": "Failed to encode image"}
        
        # Create Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create prompt based on document type
        if doc_class in ["passport_1", "passport_2"]:
            prompt = """
            Look at this passport image and check the orientation:
            
            Is the passport text readable in the correct orientation?
            - Check if text is right-side up and readable
            - Check if the passport photo is upright
            - Check if any official stamps/seals are oriented correctly
            
            Return ONLY a JSON response:
            {
                "rotation_needed": true/false,
                "rotation_angle": 90/180/270/0,
                "reason": "brief explanation"
            }
            
            Examples:
            - If passport is correctly oriented: {"rotation_needed": false, "rotation_angle": 0, "reason": "Passport is correctly oriented"}
            - If passport is upside down: {"rotation_needed": true, "rotation_angle": 180, "reason": "Passport is upside down, needs 180° rotation"}
            - If passport is sideways: {"rotation_needed": true, "rotation_angle": 90, "reason": "Passport is sideways, needs 90° rotation"}
            """
        elif doc_class == "personal_photo":
            prompt = """
            Look at this personal photo and check the orientation:
            
            Is the person's face in the correct upright orientation?
            - Check if the face is right-side up (eyes above mouth)
            - Check if the person appears to be standing/sitting normally
            - Check if any text or background elements are oriented correctly
            
            Return ONLY a JSON response:
            {
                "rotation_needed": true/false,
                "rotation_angle": 90/180/270/0,
                "reason": "brief explanation"
            }
            
            Examples:
            - If face is correctly oriented: {"rotation_needed": false, "rotation_angle": 0, "reason": "Face is correctly oriented"}
            - If face is upside down: {"rotation_needed": true, "rotation_angle": 180, "reason": "Face is upside down, needs 180° rotation"}
            - If face is sideways: {"rotation_needed": true, "rotation_angle": 90, "reason": "Face is sideways, needs 90° rotation"}
            """
        elif doc_class == "certificate":
            prompt = """
            Look at this certificate image and check the orientation:
            
            Is the certificate text readable in the correct orientation?
            - Check if text is right-side up and readable
            - Check if any official stamps/seals are oriented correctly
            - Check if the certificate layout appears normal
            
            Return ONLY a JSON response:
            {
                "rotation_needed": true/false,
                "rotation_angle": 90/180/270/0,
                "reason": "brief explanation"
            }
            
            Examples:
            - If certificate is correctly oriented: {"rotation_needed": false, "rotation_angle": 0, "reason": "Certificate is correctly oriented"}
            - If certificate is upside down: {"rotation_needed": true, "rotation_angle": 180, "reason": "Certificate is upside down, needs 180° rotation"}
            - If certificate is sideways: {"rotation_needed": true, "rotation_angle": 90, "reason": "Certificate is sideways, needs 90° rotation"}
            """
        else:
            return {"rotation_needed": False, "rotation_angle": 0, "error": "Unknown document type"}
        
        # Create image part for Gemini
        image_part = {
            "mime_type": "image/jpeg",
            "data": base64_image
        }
        
        # Generate response
        response = model.generate_content([prompt, image_part])
        content = response.text.strip()
        
        # Debug: Print raw response
        print(f"🔍 Google AI raw response: {content}")
        
        # Parse JSON response
        import json
        try:
            # Remove markdown if present
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()
            
            result = json.loads(content)
            print(f"🔍 Google AI parsed result: {result}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Gemini response as JSON: {e}")
            print(f"Raw response: {content}")
            return {"rotation_needed": False, "rotation_angle": 0, "error": f"JSON parse error: {e}"}
            
    except Exception as e:
        print(f"❌ Error in Gemini orientation detection: {e}")
        return {"rotation_needed": False, "rotation_angle": 0, "error": str(e)}

def rotate_image(image_path: str, angle: int) -> str:
    """
    Rotate image by specified angle and save to new file.
    Returns path to rotated image.
    """
    try:
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"⚠️ Could not load image: {image_path}")
            return image_path
        
        # Get image dimensions
        height, width = image.shape[:2]
        
        # Calculate rotation center
        center = (width // 2, height // 2)
        
        # Create rotation matrix
        # Note: OpenCV uses counterclockwise rotation, but we want clockwise
        # So we use negative angle for clockwise rotation
        M = cv2.getRotationMatrix2D(center, -angle, 1.0)
        
        # Calculate new image dimensions after rotation
        if angle in [90, 270]:
            new_width, new_height = height, width
        else:
            new_width, new_height = width, height
        
        # Adjust rotation matrix for new dimensions
        M[0, 2] += (new_width - width) / 2
        M[1, 2] += (new_height - height) / 2
        
        # Apply rotation
        rotated = cv2.warpAffine(image, M, (new_width, new_height), 
                                flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        
        # Save rotated image
        base_name = os.path.splitext(image_path)[0]
        rotated_path = f"{base_name}_rotated_{angle}deg.jpg"
        
        success = cv2.imwrite(rotated_path, rotated)
        
        if success:
            print(f"✅ Image rotated {angle}° clockwise and saved: {os.path.basename(rotated_path)}")
            return rotated_path
        else:
            print(f"⚠️ Failed to save rotated image")
            return image_path
            
    except Exception as e:
        print(f"❌ Error rotating image: {e}")
        return image_path

def rotate_image_if_needed_google_ai(image_path: str, doc_class: str) -> str:
    """
    Use Google AI to detect and correct image orientation.
    Only processes passport pages, personal photos, and certificates.
    """
    # Skip if not a rotatable class
    if doc_class not in ROTATABLE_CLASSES:
        print(f"↩️ Skipping rotation for class: {doc_class}")
        return image_path
    
    print(f"🔍 Using Google AI to check orientation for {doc_class}: {os.path.basename(image_path)}")
    
    # Detect orientation with Gemini
    orientation_result = detect_orientation_with_gemini(image_path, doc_class)
    
    if "error" in orientation_result:
        print(f"⚠️ Orientation detection failed: {orientation_result['error']}")
        return image_path
    
    if not orientation_result.get("rotation_needed", False):
        print(f"✅ Image orientation is correct")
        return image_path
    
    # Get rotation angle
    rotation_angle = orientation_result.get("rotation_angle", 0)
    reason = orientation_result.get("reason", "No reason provided")
    
    if rotation_angle == 0:
        print(f"✅ No rotation needed")
        return image_path
    
    print(f"🔄 Google AI detected rotation needed: {rotation_angle}° - {reason}")
    
    # Rotate the image
    rotated_path = rotate_image(image_path, rotation_angle)
    
    # Verify the rotation was successful
    if rotated_path != image_path:  # Only verify if rotation actually happened
        print(f"🔍 Verifying rotation was successful...")
        verification_result = detect_orientation_with_gemini(rotated_path, doc_class)
        
        if verification_result.get("rotation_needed", False):
            print(f"⚠️ Rotation verification failed - image still needs rotation")
            print(f"   Original angle: {rotation_angle}°, Verification result: {verification_result}")
            
            # Try additional rotation if needed
            additional_angle = verification_result.get("rotation_angle", 0)
            if additional_angle > 0:
                print(f"🔄 Attempting additional rotation of {additional_angle}°")
                final_rotated_path = rotate_image(rotated_path, additional_angle)
                
                # Final verification
                final_verification = detect_orientation_with_gemini(final_rotated_path, doc_class)
                if not final_verification.get("rotation_needed", False):
                    print(f"✅ Final rotation verification successful")
                    return final_rotated_path
                else:
                    print(f"❌ Final rotation verification failed - using original image")
                    return image_path
            else:
                print(f"❌ No additional rotation angle provided - using original image")
                return image_path
        else:
            print(f"✅ Rotation verification successful")
    
    return rotated_path 