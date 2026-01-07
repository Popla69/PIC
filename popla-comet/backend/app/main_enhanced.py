"""Enhanced FastAPI application with all features."""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import AsyncGenerator, List, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import ImageAnalysisRequest, ImageAnalysisResponse, AnalysisResult
from app.services.image_service import ImageService
from app.services.ai_service import ai_service
from app.services.batch_service import batch_processor
from app.services.websocket_service import connection_manager
from app.services.cache_service import cache_service
from app.database import init_database, AnalysisRepository, AnalyticsRepository

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
    
    init_database()
    logger.info("Database initialized")
    
    yield
    
    logger.info(f"Shutting down {settings.app_name}")


app = FastAPI(
    title=settings.app_name,
    version="0.3.0",
    description="Enhanced Computer Vision and AI-powered analysis API with real-time, batch processing, caching, and analytics",
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


# ============= Basic Endpoints =============

@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": "0.3.0",
        "status": "operational",
        "documentation": "/docs",
        "features": {
            "image_analysis": True,
            "batch_processing": True,
            "real_time_updates": True,
            "caching": True,
            "analytics": True,
            "history": True
        }
    }


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring."""
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": "0.3.0",
        "openai_configured": bool(settings.openai_api_key),
        "cache_stats": cache_service.get_stats(),
        "database": "connected"
    }
    return JSONResponse(content=health_status, status_code=200)


@app.get("/api/v1/status")
async def api_status() -> dict:
    """API status endpoint with detailed information."""
    stats = AnalyticsRepository.get_statistics()
    
    return {
        "api_version": "v1",
        "service": settings.app_name,
        "status": "operational",
        "features": {
            "image_analysis": bool(settings.openai_api_key),
            "object_detection": True,
            "image_processing": True,
            "batch_processing": True,
            "real_time_updates": True,
            "caching": True
        },
        "statistics": stats
    }


# ============= Image Analysis Endpoints =============

@app.post("/api/v1/analyze", response_model=ImageAnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    prompt: str = Form(None),
    user_id: str = Form(None),
    use_cache: bool = Form(True)
) -> ImageAnalysisResponse:
    """Analyze an uploaded image with optional caching."""
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    
    try:
        image_data = await file.read()
        
        is_valid, error_msg = image_service.validate_image(image_data)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        if use_cache:
            cached_result = cache_service.get(image_data)
            if cached_result:
                logger.info(f"Returning cached result for analysis {analysis_id}")
                return ImageAnalysisResponse(
                    analysis_id=analysis_id,
                    timestamp=datetime.now(),
                    status="completed",
                    result=AnalysisResult(**cached_result),
                    error=None,
                    processing_time=time.time() - start_time
                )
        
        logger.info(f"Processing image analysis request {analysis_id}")
        
        AnalyticsRepository.track_event("analysis_started", {
            "analysis_id": analysis_id,
            "image_size": len(image_data)
        }, user_id)
        
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
        
        if use_cache:
            cache_service.set(image_data, result.dict())
        
        processing_time = time.time() - start_time
        
        AnalysisRepository.save_result(
            analysis_id=analysis_id,
            status="completed",
            processing_time=processing_time,
            description=result.description,
            confidence=result.confidence,
            tags=result.tags,
            objects_detected=result.objects_detected,
            user_id=user_id,
            image_size=len(image_data)
        )
        
        AnalyticsRepository.track_event("analysis_completed", {
            "analysis_id": analysis_id,
            "processing_time": processing_time
        }, user_id)
        
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
        
        AnalysisRepository.save_result(
            analysis_id=analysis_id,
            status="failed",
            processing_time=processing_time,
            error=str(e),
            user_id=user_id
        )
        
        return ImageAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            status="failed",
            result=None,
            error=str(e),
            processing_time=processing_time
        )


@app.post("/api/v1/analyze/base64", response_model=ImageAnalysisResponse)
async def analyze_image_base64(
    request: ImageAnalysisRequest,
    user_id: Optional[str] = None
) -> ImageAnalysisResponse:
    """Analyze a base64 encoded image."""
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
        
        ai_result = await ai_service.analyze_image(image_data, request.prompt)
        
        result = AnalysisResult(
            description=ai_result.get("description", "Analysis completed"),
            confidence=ai_result.get("confidence", 0.8),
            tags=ai_result.get("tags", []),
            objects_detected=ai_result.get("objects_detected", [])
        )
        
        processing_time = time.time() - start_time
        
        AnalysisRepository.save_result(
            analysis_id=analysis_id,
            status="completed",
            processing_time=processing_time,
            description=result.description,
            confidence=result.confidence,
            tags=result.tags,
            objects_detected=result.objects_detected,
            user_id=user_id
        )
        
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
        return ImageAnalysisResponse(
            analysis_id=analysis_id,
            timestamp=datetime.now(),
            status="failed",
            result=None,
            error=str(e),
            processing_time=time.time() - start_time
        )


# ============= Batch Processing Endpoints =============

@app.post("/api/v1/batch/analyze")
async def batch_analyze(
    files: List[UploadFile] = File(...),
    user_id: Optional[str] = Form(None)
):
    """Analyze multiple images in batch."""
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 images per batch")
    
    try:
        images = []
        for file in files:
            image_data = await file.read()
            is_valid, error_msg = image_service.validate_image(image_data)
            if is_valid:
                images.append(image_data)
        
        if not images:
            raise HTTPException(status_code=400, detail="No valid images in batch")
        
        AnalyticsRepository.track_event("batch_started", {
            "image_count": len(images)
        }, user_id)
        
        result = await batch_processor.process_batch(images)
        
        AnalyticsRepository.track_event("batch_completed", {
            "batch_id": result["batch_id"],
            "total": result["total_images"],
            "successful": result["successful"]
        }, user_id)
        
        return result
        
    except Exception as e:
        logger.error(f"Batch processing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/batch/{batch_id}/status")
async def get_batch_status(batch_id: str):
    """Get status of a batch processing job."""
    status = batch_processor.get_batch_status(batch_id)
    if status.get("status") == "not_found":
        raise HTTPException(status_code=404, detail="Batch not found")
    return status


# ============= History & Analytics Endpoints =============

@app.get("/api/v1/history")
async def get_history(
    user_id: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
):
    """Get analysis history."""
    if user_id:
        results = AnalysisRepository.get_user_history(user_id, limit)
    else:
        results = AnalysisRepository.get_recent_analyses(limit)
    
    return {
        "total": len(results),
        "results": results
    }


@app.get("/api/v1/analytics")
async def get_analytics():
    """Get system analytics and statistics."""
    stats = AnalyticsRepository.get_statistics()
    cache_stats = cache_service.get_stats()
    
    return {
        "system": stats,
        "cache": cache_stats,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/v1/result/{analysis_id}")
async def get_result(analysis_id: str):
    """Get a specific analysis result."""
    result = AnalysisRepository.get_result(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


# ============= WebSocket Endpoint =============

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates."""
    await connection_manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            if data == "ping":
                await connection_manager.send_personal_message(
                    {"type": "pong"},
                    websocket
                )
            
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, client_id)
        logger.info(f"Client {client_id} disconnected")


# ============= Cache Management Endpoints =============

@app.post("/api/v1/cache/clear")
async def clear_cache():
    """Clear the analysis cache."""
    cache_service.clear()
    return {"message": "Cache cleared successfully"}


@app.get("/api/v1/cache/stats")
async def get_cache_stats():
    """Get cache statistics."""
    return cache_service.get_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main_enhanced:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
