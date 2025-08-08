from ultralytics import YOLO
import cv2
import os

# === CONFIGURATION ===
model_path = os.getenv("YOLO_MODEL_PATH", "models/yolo8_best.pt")

# Load model (only load once, not run processing)
model = YOLO(model_path)

def run_yolo_crop(image_path: str, temp_dir: str) -> str:
    """
    Run YOLO cropping on a single image.
    
    Args:
        image_path: Path to the input image
        temp_dir: Directory to save cropped images
    
    Returns:
        str: Path to the cropped image (or original if no detections)
    """
    try:
        # Read the image
        image = cv2.imread(image_path)
        if image is None:
            print(f"⚠️ Could not read image: {image_path}")
            return image_path
        
        # Run YOLO detection
        results = model(image)[0]
        
        if not results.boxes:
            print(f"ℹ️ No detections in image: {os.path.basename(image_path)}")
            return image_path
        
        # Get the first detection (most confident)
        box = results.boxes[0]
        x1, y1, x2, y2 = map(int, box.xyxy[0])
        
        # Crop the image
        cropped = image[y1:y2, x1:x2]
        
        # Save cropped image
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        crop_name = f"{base_name}_cropped.jpg"
        crop_path = os.path.join(temp_dir, crop_name)
        
        cv2.imwrite(crop_path, cropped)
        print(f"✅ Cropped image saved: {crop_name}")
        
        return crop_path
        
    except Exception as e:
        print(f"❌ Error cropping image {image_path}: {e}")
        return image_path
