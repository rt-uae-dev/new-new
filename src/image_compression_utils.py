from PIL import Image
import os

def compress_image_to_jpg(image_path: str, output_path: str, max_kb: int = 110) -> str:
    """
    Compress an image to JPEG format under a max file size in kilobytes.
    If needed, reduce dimensions to meet the size constraint.
    Optimized for document images that need to remain readable.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img = Image.open(image_path).convert("RGB")

    # Use modern resampling filter
    try:
        resample = Image.Resampling.LANCZOS
    except AttributeError:
        resample = Image.ANTIALIAS  # For backward compatibility

    quality = 85  # Start with lower quality for more aggressive compression
    img.save(output_path, "JPEG", quality=quality)

    # Try reducing quality more aggressively
    min_quality = 20  # Lower minimum quality to get below 110KB
    while os.path.getsize(output_path) > max_kb * 1024 and quality > min_quality:
        quality -= 10  # Reduce quality more aggressively
        img.save(output_path, "JPEG", quality=quality)

    # Resize if still too large, be more aggressive with resizing
    if os.path.getsize(output_path) > max_kb * 1024:
        width, height = img.size
        min_width = 400  # Lower minimum width for more aggressive compression
        while os.path.getsize(output_path) > max_kb * 1024 and width > min_width:
            width = int(width * 0.8)  # Reduce size more aggressively (20% reduction)
            height = int(height * 0.8)
            resized = img.resize((width, height), resample)
            resized.save(output_path, "JPEG", quality=quality)

    # Final check
    final_kb = os.path.getsize(output_path) / 1024
    if final_kb > max_kb:
        print(f"⚠️ Warning: Could not compress below {max_kb}KB. Final size: {final_kb:.2f}KB")
        # Don't raise error, just warn and continue

    print(f"✅ Compressed {os.path.basename(image_path)} to {final_kb:.1f}KB (quality={quality})")
    return output_path
