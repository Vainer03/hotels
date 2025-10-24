from fastapi import APIRouter

router = APIRouter(tags=["general"])

@router.get("/")
async def root():
    return {
        "message": "Hotel Booking API is running!",
        "version": "2.2.0",
        "status": "healthy",
        "docs": "/api/v1/docs",
        "health": "/api/v1/health"
    }

@router.get("/health")
async def health_check():
    return {"status": "healthy"}