"""Image processing and validation service."""

import base64
import io
from typing import Tuple, Optional
from PIL import Image
import cv2
import numpy as np

from app.config import settings


class ImageService:
    """Service for image processing and validation."""
    
    @staticmethod
    def validate_image(image_data: bytes) -> Tuple[bool, Optional[str]]:
        """
        Validate image data.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if len(image_data) > settings.max_upload_size:
                return False, f"Image size exceeds maximum of {settings.max_upload_size} bytes"
            
            image = Image.open(io.BytesIO(image_data))
            
            if image.format.lower() not in ['jpeg', 'jpg', 'png', 'webp']:
                return False, f"Unsupported image format: {image.format}"
            
            if image.width > 4096 or image.height > 4096:
                return False, "Image dimensions exceed maximum of 4096x4096"
            
            return True, None
            
        except Exception as e:
            return False, f"Invalid image data: {str(e)}"
    
    @staticmethod
    def decode_base64_image(base64_data: str) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Decode base64 encoded image.
        
        Args:
            base64_data: Base64 encoded image string
            
        Returns:
            Tuple of (image_bytes, error_message)
        """
        try:
            if ',' in base64_data:
                base64_data = base64_data.split(',')[1]
            
            image_data = base64.b64decode(base64_data)
            return image_data, None
            
        except Exception as e:
            return None, f"Failed to decode image: {str(e)}"
    
    @staticmethod
    def process_image(image_data: bytes) -> dict:
        """
        Process image with OpenCV to extract basic features.
        
        Args:
            image_data: Raw image bytes
            
        Returns:
            Dictionary with image features
        """
        try:
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return {"error": "Failed to decode image"}
            
            height, width = img.shape[:2]
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            brightness = np.mean(gray)
            
            edges = cv2.Canny(gray, 100, 200)
            edge_density = np.sum(edges > 0) / (width * height)
            
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            return {
                "width": int(width),
                "height": int(height),
                "brightness": float(brightness),
                "edge_density": float(edge_density),
                "sharpness": float(blur_score),
                "is_blurry": blur_score < 100
            }
            
        except Exception as e:
            return {"error": f"Image processing failed: {str(e)}"}
    
    @staticmethod
    def resize_image(image_data: bytes, max_size: int = 1024) -> bytes:
        """
        Resize image maintaining aspect ratio.
        
        Args:
            image_data: Raw image bytes
            max_size: Maximum dimension
            
        Returns:
            Resized image bytes
        """
        try:
            image = Image.open(io.BytesIO(image_data))
            
            if max(image.width, image.height) <= max_size:
                return image_data
            
            ratio = max_size / max(image.width, image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            
            resized = image.resize(new_size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            resized.save(output, format=image.format or 'PNG')
            
            return output.getvalue()
            
        except Exception:
            return image_data
