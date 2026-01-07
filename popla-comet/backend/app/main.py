"""FastAPI application entry point for Popla Comet backend."""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import ImageAnalysisRequest, ImageAnalysisResponse, AnalysisResult
from app.services.image_service import ImageService
from app.services.ai_service import ai_service

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context manager for startup and shutdown events."""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"OpenAI API configured: {bool(settings.openai_api_key)}")
    yield
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Computer vision and AI-powered analysis API for Popla Comet mobile app",
    lifespan=lifespan,
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=settings.cors_methods,
    allow_headers=settings.cors_headers,
)

image_service = ImageService()


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "documentation": "/docs"
    }


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring and load balancers."""
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "openai_configured": bool(settings.openai_api_key),
    }
    return JSONResponse(content=health_status, status_code=200)


@app.get("/api/v1/status")
async def api_status() -> dict:
    """API status endpoint with detailed service information."""
    return {
        "api_version": "v1",
        "service": settings.app_name,
        "status": "operational",
        "features": {
            "image_analysis": bool(settings.openai_api_key),
            "object_detection": True,
            "image_processing": True,
        }
    }


@app.post("/api/v1/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form(None)
) -> ImageAnalysisResponse:
    """
    Analyze an uploaded image using AI.
    
    Args:
        file: Image file to analyze
        prompt: Optional custom analysis prompt
        
    Returns:
        Analysis results
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    try:
        image_data = await file.read()
        
        is_valid, error_msg = image_service.validate_image(image_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        logger.info(f"Processing image analysis request {analysis_id}")
        
        cv_features = image_service.process_image(image_data)
        
        ai_result = await ai_service.analyze_image(image_data, prompt)
        
        if "error" in ai_result and not ai_result.get("description"):
            result = AnalysisResult(
                description=f"Image processing completed. {ai_result['error']}",
                confidence=0.5,
                tags=["processed"],
                objects_detected=[]
            )
        else:
            result = AnalysisResult(
                description=ai_result.get("description", "Analysis completed"),
                confidence=ai_result.get("confidence", 0.8),
                tags=ai_result.get("tags", []),
                objects_detected=ai_result.get("objects_detected", [])
            )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Analysis {analysis_id} completed in {processing_time:.2f}s")
        
        return ImageAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            status="completed",
            result=result,
            error=None,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}")
        processing_time = time.time() - start_time
        
        return ImageAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            status="failed",
            result=None,
            error=str(e),
            processing_time=processing_time
        )


@app.post("/api/v1/analyze/base64", response_model=ImageAnalysisResponse)
async def analyze_image_base64(request: ImageAnalysisRequest) -> ImageAnalysisResponse:
    """
    Analyze a base64 encoded image.
    
    Args:
        request: Image analysis request with base64 data
        
    Returns:
        Analysis results
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    try:
        image_data, decode_error = image_service.decode_base64_image(request.image_data)
        if decode_error:
            raise HTTPException(status_code=400, detail=decode_error)
        
        is_valid, error_msg = image_service.validate_image(image_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        logger.info(f"Processing base64 image analysis request {analysis_id}")
        
        cv_features = image_service.process_image(image_data)
        
        ai_result = await ai_service.analyze_image(image_data, request.prompt)
        
        if "error" in ai_result and not ai_result.get("description"):
            result = AnalysisResult(
                description=f"Image processing completed. {ai_result['error']}",
                confidence=0.5,
                tags=["processed"],
                objects_detected=[]
            )
        else:
            result = AnalysisResult(
                description=ai_result.get("description", "Analysis completed"),
                confidence=ai_result.get("confidence", 0.8),
                tags=ai_result.get("tags", []),
                objects_detected=ai_result.get("objects_detected", [])
            )
        
        processing_time = time.time() - start_time
        
        logger.info(f"Analysis {analysis_id} completed in {processing_time:.2f}s")
        
        return ImageAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            status="completed",
            result=result,
            error=None,
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis {analysis_id} failed: {str(e)}")
        processing_time = time.time() - start_time
        
        return ImageAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            status="failed",
            result=None,
            error=str(e),
            processing_time=processing_time
        )


@app.post("/api/v1/process")
async def process_image(file: UploadFile = File(...)) -> dict:
    """
    Process image with OpenCV to extract features.
    
    Args:
        file: Image file to process
        
    Returns:
        Image features
    """
    try:
        image_data = await file.read()
        
        is_valid, error_msg = image_service.validate_image(image_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        features = image_service.process_image(image_data)
        
        return {
            "status": "success",
            "features": features
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
