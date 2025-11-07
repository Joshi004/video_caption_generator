from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

from .routers import videos
from .services.model_client import ModelServiceClient
from .schemas.video_schema import HealthCheck

# Create FastAPI app
app = FastAPI(
    title="Video Caption Service API",
    description="Backend API for video captioning using OmniVinci",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(videos.router)

# Model service client
model_client = ModelServiceClient()


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Video Caption Service",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    # Check model service health (using default model)
    try:
        from .services.model_client import VLLMClient
        default_model = os.getenv("DEFAULT_MODEL", "qwen2vl")
        client = VLLMClient(model_key=default_model)
        model_service_health = await client.health_check()
        model_service_healthy = model_service_health.get("status") == "healthy"
        model_url = client.vllm_url
    except Exception as e:
        model_service_healthy = False
        model_url = "unknown"
    
    return HealthCheck(
        status="healthy" if model_service_healthy else "degraded",
        backend_healthy=True,
        model_service_healthy=model_service_healthy,
        model_service_url=model_url
    )


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)



