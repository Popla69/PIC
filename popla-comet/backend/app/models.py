"""Data models for Popla Comet backend."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ImageAnalysisRequest(BaseModel):
    """Request model for image analysis."""
    image_data: str = Field(..., description="Base64 encoded image data")
    analysis_type: str = Field(default="general", description="Type of analysis to perform")
    prompt: Optional[str] = Field(None, description="Custom prompt for analysis")


class AnalysisResult(BaseModel):
    """Model for analysis results."""
    description: str
    confidence: float = Field(ge=0.0, le=1.0)
    tags: List[str] = []
    objects_detected: List[str] = []


class ImageAnalysisResponse(BaseModel):
    """Response model for image analysis."""
    analysis_id: str
    timestamp: datetime
    status: str
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None
    processing_time: float


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    openai_configured: bool
