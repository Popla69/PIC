"""AI service for image analysis using OpenAI."""

import base64
from typing import Dict, List, Optional
from openai import AsyncOpenAI
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered image analysis."""
    
    def __init__(self):
        """Initialize the AI service."""
        self.client = None
        if settings.openai_api_key:
            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
    
    async def analyze_image(
        self,
        image_data: bytes,
        prompt: Optional[str] = None
    ) -> Dict:
        """
        Analyze image using OpenAI GPT-4 Vision.
        
        Args:
            image_data: Raw image bytes
            prompt: Optional custom prompt
            
        Returns:
            Analysis results dictionary
        """
        if not self.client:
            return {
                "error": "OpenAI API not configured",
                "description": "AI analysis unavailable - API key not provided",
                "confidence": 0.0,
                "tags": [],
                "objects_detected": []
            }
        
        try:
            base64_image = base64.b64encode(image_data).decode('utf-8')
            
            default_prompt = (
                "Analyze this image in detail. Provide:\n"
                "1. A comprehensive description of what you see\n"
                "2. List of main objects detected\n"
                "3. Relevant tags/keywords\n"
                "4. Any notable features or patterns\n"
                "Format your response as a structured analysis."
            )
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt or default_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            response = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=settings.openai_max_tokens,
            )
            
            analysis_text = response.choices[0].message.content
            
            result = self._parse_analysis(analysis_text)
            result["raw_response"] = analysis_text
            
            return result
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {
                "error": str(e),
                "description": f"Analysis failed: {str(e)}",
                "confidence": 0.0,
                "tags": [],
                "objects_detected": []
            }
    
    def _parse_analysis(self, analysis_text: str) -> Dict:
        """
        Parse analysis text to extract structured data.
        
        Args:
            analysis_text: Raw analysis text
            
        Returns:
            Structured analysis dictionary
        """
        lines = analysis_text.split('\n')
        
        description = analysis_text
        objects = []
        tags = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            if 'objects' in line_lower or 'detected' in line_lower:
                if i + 1 < len(lines):
                    objects_text = lines[i + 1]
                    objects = [
                        obj.strip(' -•*')
                        for obj in objects_text.split(',')
                        if obj.strip()
                    ]
            
            if 'tags' in line_lower or 'keywords' in line_lower:
                if i + 1 < len(lines):
                    tags_text = lines[i + 1]
                    tags = [
                        tag.strip(' -•*#')
                        for tag in tags_text.split(',')
                        if tag.strip()
                    ]
        
        if not objects:
            objects = self._extract_nouns(analysis_text[:200])
        
        if not tags:
            tags = self._generate_tags(analysis_text)
        
        confidence = 0.85 if len(analysis_text) > 50 else 0.5
        
        return {
            "description": description,
            "confidence": confidence,
            "tags": tags[:10],
            "objects_detected": objects[:15]
        }
    
    def _extract_nouns(self, text: str) -> List[str]:
        """Extract potential object names from text."""
        common_objects = [
            'person', 'people', 'man', 'woman', 'child',
            'car', 'vehicle', 'building', 'tree', 'sky',
            'water', 'mountain', 'road', 'house', 'animal',
            'dog', 'cat', 'bird', 'flower', 'plant'
        ]
        
        text_lower = text.lower()
        found = [obj for obj in common_objects if obj in text_lower]
        
        return found[:5]
    
    def _generate_tags(self, text: str) -> List[str]:
        """Generate tags from analysis text."""
        text_lower = text.lower()
        
        tag_keywords = {
            'outdoor': ['outdoor', 'outside', 'nature', 'landscape'],
            'indoor': ['indoor', 'inside', 'room', 'interior'],
            'people': ['person', 'people', 'human', 'man', 'woman'],
            'animal': ['animal', 'dog', 'cat', 'bird', 'pet'],
            'nature': ['nature', 'tree', 'plant', 'flower', 'forest'],
            'urban': ['city', 'urban', 'building', 'street', 'road'],
            'vehicle': ['car', 'vehicle', 'bike', 'motorcycle', 'truck'],
            'food': ['food', 'meal', 'dish', 'cuisine'],
            'technology': ['computer', 'phone', 'device', 'technology'],
            'art': ['art', 'painting', 'sculpture', 'artwork']
        }
        
        tags = []
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags


ai_service = AIService()
