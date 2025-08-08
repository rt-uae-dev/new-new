#!/usr/bin/env python3
"""
Document Processing Module
Handles PDF conversion, image classification, rotation, YOLO cropping, and OCR
"""

import os
from typing import List, Dict, Any
from pdf_converter import convert_pdf_to_jpg
from resnet18_classifier import classify_image_resnet
from simple_gemini_rotation import rotate_if_needed
from crop_yolo_detections import run_yolo_crop
from yolo_crop_ocr_pipeline import run_enhanced_ocr
from image_utils import compress_image_to_jpg
from output_saving_utils import safe_copy_file

def convert_pdfs_to_images(subject_path: str, temp_dir: str) -> List[str]:
    """Convert PDFs to JPGs and copy existing images to temp directory."""
    print("🔄 Converting PDFs to JPGs...")
    all_image_paths = []
    
    for filename in os.listdir(subject_path):
        file_path = os.path.join(subject_path, filename)
        if filename.lower().endswith(".pdf"):
            print(f"📄 Converting: {filename}")
            jpg_paths = convert_pdf_to_jpg(file_path, temp_dir)
            all_image_paths.extend(jpg_paths)
        elif filename.lower().endswith((".jpg", ".jpeg", ".png")):
            # Copy existing images to temp without compression (for best OCR quality)
            temp_path = os.path.join(temp_dir, filename)
            if safe_copy_file(file_path, temp_path):
                all_image_paths.append(temp_path)
                print(f"📷 Copied image: {filename}")
            else:
                print(f"⚠️ Failed to copy image: {filename}")
    
    return all_image_paths

def classify_images(all_image_paths: List[str]) -> List[Dict[str, Any]]:
    """Classify all images with ResNet."""
    print("🏷️ Classifying images with ResNet...")
    classified_images = []
    
    for img_path in all_image_paths:
        try:
            resnet_label = classify_image_resnet(img_path)
            classified_images.append({
                "path": img_path,
                "label": resnet_label,
                "filename": os.path.basename(img_path)
            })
            print(f"✅ {os.path.basename(img_path)} → {resnet_label}")
        except Exception as e:
            print(f"❌ Error classifying {os.path.basename(img_path)}: {e}")
    
    return classified_images

def handle_certificate_attestation_pairing(classified_images: List[Dict[str, Any]]) -> None:
    """Ensure certificate + attestation pairing."""
    has_certificate = any(img["label"] == "certificate" for img in classified_images)
    has_attestation = any(img["label"] in ["certificate_attestation", "attestation_label"] for img in classified_images)
    
    if has_certificate and not has_attestation:
        print("⚠️ Certificate found but no attestation page. Looking for misclassified attestation...")
        for img_data in classified_images:
            if img_data["label"] in ["emirates_id", "emirates_id_2", "unknown"]:
                # Reclassify as attestation_label for further processing
                img_data["label"] = "attestation_label"
                print(f"🔄 Reclassified {img_data['filename']} as attestation_label")

def rotate_images_if_needed(classified_images: List[Dict[str, Any]]) -> None:
    """Rotate images if needed using Gemini 2.5 Flash (only specific document types)."""
    print("🔄 Using Gemini 2.5 Flash to check and rotate images if needed...")
    
    # Check if we have passport pages that need special handling
    passport_1_images = [img for img in classified_images if img["label"] == "passport_1"]
    passport_2_images = [img for img in classified_images if img["label"] == "passport_2"]
    
    # Define rotation check types
    rotation_check_types = ["passport_1", "passport_2", "personal_photo", "certificate"]
    
    if passport_1_images or passport_2_images:
        print("🔄 Detected passport pages - using enhanced multi-page rotation...")
        from simple_gemini_rotation import rotate_multi_page_documents
        rotate_multi_page_documents(classified_images)
        
        # Also process other document types (certificates, personal photos) after passport rotation
        print("🔄 Processing other document types after passport rotation...")
        for img_data in classified_images:
            try:
                # Only check rotation for specific document types that are not passports
                if img_data["label"] in ["personal_photo", "certificate"]:
                    print(f"🔍 Checking rotation for {img_data['filename']} ({img_data['label']})...")
                    rotated_path = rotate_if_needed(img_data["path"], is_passport_page=False)
                    if rotated_path != img_data["path"]:
                        img_data["rotated_path"] = rotated_path
                        print(f"✅ Gemini 2.5 Flash rotation applied to {img_data['filename']} ({img_data['label']})")
                    else:
                        print(f"✅ No rotation needed for {img_data['filename']} ({img_data['label']})")
            except Exception as e:
                print(f"⚠️ Error rotating {img_data['filename']}: {e}")
    else:
        # Only check rotation for specific document types after classification
        for img_data in classified_images:
            try:
                # Only check rotation for specific document types
                if img_data["label"] in rotation_check_types:
                    print(f"🔍 Checking rotation for {img_data['filename']} ({img_data['label']})...")
                    # Use passport-specific prompt for passport pages
                    is_passport = img_data["label"] in ["passport_1", "passport_2"]
                    rotated_path = rotate_if_needed(img_data["path"], is_passport_page=is_passport)
                    if rotated_path != img_data["path"]:
                        img_data["rotated_path"] = rotated_path
                        print(f"✅ Gemini 2.5 Flash rotation applied to {img_data['filename']} ({img_data['label']})")
                    else:
                        print(f"✅ No rotation needed for {img_data['filename']} ({img_data['label']})")
                else:
                    print(f"⏭️ Skipping rotation check for {img_data['filename']} ({img_data['label']}) - not in rotation check list")
            except Exception as e:
                print(f"⚠️ Error rotating {img_data['filename']}: {e}")

def process_attestation_pages(classified_images: List[Dict[str, Any]], temp_dir: str, output_dir: str, current_subject_folder: str) -> None:
    """Process attestation pages detected by ResNet."""
    print("📋 Checking for attestation pages detected by ResNet...")
    attestation_images = [img for img in classified_images if img["label"] in ["certificate_attestation", "attestation_label"]]
    
    for attestation_img in attestation_images:
        try:
            # Compress attestation page first
            compressed_path = compress_image_to_jpg(
                attestation_img["path"],
                os.path.join(temp_dir, f"{os.path.splitext(os.path.basename(attestation_img['path']))[0]}_compressed.jpg")
            )
            attestation_img["compressed_path"] = compressed_path
            print(f"✅ Compressed attestation page: {os.path.basename(attestation_img['path'])}")
            
            # Copy to finished folder immediately
            finished_folder = os.path.join(output_dir, current_subject_folder)
            os.makedirs(finished_folder, exist_ok=True)
            finished_path = os.path.join(finished_folder, f"{os.path.splitext(os.path.basename(attestation_img['path']))[0]}_attestation_label.jpg")
            if safe_copy_file(compressed_path, finished_path):
                attestation_img["finished_path"] = finished_path
                print(f"✅ Copied attestation page to finished folder: {os.path.basename(finished_path)}")
            else:
                print(f"⚠️ Failed to copy attestation page to finished folder")
        except Exception as e:
            print(f"❌ Error processing attestation {attestation_img['filename']}: {e}")

def run_yolo_cropping(classified_images: List[Dict[str, Any]], temp_dir: str) -> None:
    """Run YOLO cropping for ALL documents."""
    print("✂️ Running YOLO cropping for ALL documents...")
    for img_data in classified_images:
        try:
            # Use the rotated path if available, otherwise use the original path
            # This ensures we crop from the correctly oriented image
            input_path = img_data.get("rotated_path", img_data["path"])
            
            # Run YOLO cropping for ALL documents
            cropped_path = run_yolo_crop(input_path, temp_dir)
            img_data["cropped_path"] = cropped_path
            print(f"✅ YOLO cropped {img_data['label']}: {os.path.basename(cropped_path)}")
            
        except Exception as e:
            print(f"❌ Error cropping {img_data['filename']}: {e}")

def run_ocr_processing(classified_images: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run OCR for all documents using cropped versions."""
    print("📝 Running OCR for all documents using cropped versions...")
    processed_images = []
    
    for img_data in classified_images:
        try:
            # Skip OCR for personal photos since they don't contain text
            if img_data["label"] == "personal_photo":
                print(f"⏭️ Skipping OCR for personal photo: {img_data['filename']}")
                img_data["ocr_text"] = ""
                img_data["extracted_fields"] = {}
                img_data["document_type"] = "personal_photo"
                img_data["confidence"] = 1.0
                processed_images.append(img_data)
                continue
            
            # Use cropped path for OCR (all other documents)
            ocr_path = img_data["cropped_path"]

            # Run OCR
            vision_data = run_enhanced_ocr(ocr_path)
            img_data["ocr_text"] = vision_data.get("ocr_text", "")
            img_data["extracted_fields"] = vision_data.get("extracted_fields", {})
            img_data["document_type"] = vision_data.get("document_type", "unknown")
            img_data["confidence"] = vision_data.get("confidence", 0.0)
            
            processed_images.append(img_data)
            print(f"✅ OCR completed: {img_data['filename']} ({img_data['label']})")
            
        except Exception as e:
            print(f"❌ Error processing {img_data['filename']}: {e}")
            # Still add to processed_images even if OCR fails, with empty data
            img_data["ocr_text"] = ""
            img_data["extracted_fields"] = {}
            img_data["document_type"] = "unknown"
            img_data["confidence"] = 0.0
            processed_images.append(img_data)
            print(f"⚠️ Added {img_data['filename']} to processed list despite OCR error")

    if not processed_images:
        if classified_images:
            print(f"⚠️ OCR failed for all images, but proceeding with empty OCR data")
            # Use classified_images as processed_images with empty OCR data
            for img_data in classified_images:
                img_data["ocr_text"] = ""
                img_data["extracted_fields"] = {}
                img_data["document_type"] = "unknown"
                img_data["confidence"] = 0.0
            processed_images = classified_images
        else:
            print(f"⚠️ No processed images. Skipping folder.")
            return []

    return processed_images
