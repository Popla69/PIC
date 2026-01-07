"""Batch processing service for multiple images."""

import asyncio
from typing import List, Dict
from datetime import datetime
import uuid
import logging

from app.services.image_service import ImageService
from app.services.ai_service import ai_service

logger = logging.getLogger(__name__)


class BatchProcessor:
    """Process multiple images in batch."""
    
    def __init__(self):
        self.image_service = ImageService()
        self.active_batches: Dict[str, Dict] = {}
    
    async def process_batch(
        self,
        images: List[bytes],
        prompts: List[str] = None
    ) -> Dict:
        """
        Process multiple images in batch.
        
        Args:
            images: List of image bytes
            prompts: Optional list of prompts (one per image)
            
        Returns:
            Batch processing results
        """
        batch_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        self.active_batches[batch_id] = {
            "status": "processing",
            "total": len(images),
            "completed": 0,
            "results": []
        }
        
        try:
            tasks = []
            for i, image_data in enumerate(images):
                prompt = prompts[i] if prompts and i < len(prompts) else None
                task = self._process_single_image(batch_id, i, image_data, prompt)
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            successful = sum(1 for r in results if not isinstance(r, Exception) and r.get("status") == "success")
            failed = len(results) - successful
            
            batch_result = {
                "batch_id": batch_id,
                "total_images": len(images),
                "successful": successful,
                "failed": failed,
                "processing_time": processing_time,
                "results": [r if not isinstance(r, Exception) else {"status": "error", "error": str(r)} for r in results]
            }
            
            self.active_batches[batch_id] = {
                "status": "completed",
                "result": batch_result
            }
            
            return batch_result
            
        except Exception as e:
            logger.error(f"Batch processing failed: {str(e)}")
            self.active_batches[batch_id] = {
                "status": "failed",
                "error": str(e)
            }
            raise
    
    async def _process_single_image(
        self,
        batch_id: str,
        index: int,
        image_data: bytes,
        prompt: str = None
    ) -> Dict:
        """Process a single image in the batch."""
        try:
            is_valid, error_msg = self.image_service.validate_image(image_data)
            if not is_valid:
                return {
                    "index": index,
                    "status": "error",
                    "error": error_msg
                }
            
            features = self.image_service.process_image(image_data)
            
            ai_result = await ai_service.analyze_image(image_data, prompt)
            
            result = {
                "index": index,
                "status": "success",
                "description": ai_result.get("description", "Analysis completed"),
                "confidence": ai_result.get("confidence", 0.8),
                "tags": ai_result.get("tags", []),
                "objects_detected": ai_result.get("objects_detected", []),
                "features": features
            }
            
            self.active_batches[batch_id]["completed"] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"Image {index} processing failed: {str(e)}")
            return {
                "index": index,
                "status": "error",
                "error": str(e)
            }
    
    def get_batch_status(self, batch_id: str) -> Dict:
        """Get status of a batch processing job."""
        return self.active_batches.get(batch_id, {"status": "not_found"})
    
    def clear_completed_batches(self, max_age_hours: int = 24):
        """Clear old completed batches from memory."""
        to_remove = []
        for batch_id, batch_data in self.active_batches.items():
            if batch_data.get("status") in ["completed", "failed"]:
                to_remove.append(batch_id)
        
        for batch_id in to_remove[:100]:
            del self.active_batches[batch_id]


batch_processor = BatchProcessor()
