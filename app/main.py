import uvicorn
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.database import create_tables
from app.core.rabbitmq import rabbitmq_manager, RabbitMQManager
from app.core.redis import redis_manager, RedisManager
from app.routers.hotels import router as hotels_router
from app.routers.rooms import router as rooms_router
from app.routers.users import router as users_router
from app.routers.bookings import router as bookings_router
from app.routers.tasks import router as tasks_router
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Hotel Booking API...")
    
    try:
        create_tables()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    
    try:
        global rabbitmq_manager
        rabbitmq_manager = RabbitMQManager()  
        await rabbitmq_manager.connect()
    except Exception as e:
        logger.error(f"RabbitMQ error: {e}")
    
    try:
        global redis_manager
        redis_manager = RedisManager()  
        await redis_manager.connect()
    except Exception as e:
        logger.error(f"Redis error: {e}")
    
    logger.info("All services initialized")
    yield
    
    logger.info("Shutting down Hotel Booking API...")
    
    try:
        if rabbitmq_manager:
            await rabbitmq_manager.close()
    except Exception as e:
        logger.error(f"RabbitMQ shutdown error: {e}")
    
    try:
        if redis_manager:
            await redis_manager.close()
    except Exception as e:
        logger.error(f"Redis shutdown error: {e}")

app = FastAPI(
    title="Hotel Booking API",
    description="Полнофункциональное API для бронирования отелей с RabbitMQ, Redis и Celery",
    version="2.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "message": "Hotel Booking API is running!",
        "version": "2.2.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    services = {
        "api": "healthy",
        "database": "unknown",
        "rabbitmq": "unknown", 
        "redis": "unknown"
    }
    
    try:
        from app.database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        services["database"] = "healthy"
    except Exception as e:
        services["database"] = f"unhealthy: {str(e)}"
    
    try:
        if rabbitmq_manager and rabbitmq_manager.connection:
            services["rabbitmq"] = "healthy"
        else:
            services["rabbitmq"] = "unavailable"
    except Exception as e:
        services["rabbitmq"] = f"unhealthy: {str(e)}"
    
    try:
        if redis_manager and redis_manager.redis:
            await redis_manager.redis.ping()
            services["redis"] = "healthy"
        else:
            services["redis"] = "unavailable"
    except Exception as e:
        services["redis"] = f"unhealthy: {str(e)}"
    
    critical_services = ["api", "database"]
    degraded_services = ["rabbitmq", "redis"]
    
    critical_healthy = all(services[svc] == "healthy" for svc in critical_services)
    degraded_healthy = all(services[svc] in ["healthy", "unavailable"] for svc in degraded_services)
    
    if critical_healthy and degraded_healthy:
        overall_status = "healthy"
    elif critical_healthy:
        overall_status = "degraded"
    else:
        overall_status = "unhealthy"
    
    return {
        "status": overall_status,
        "services": services,
        "timestamp": "2024-01-01T00:00:00Z"
    }

app.include_router(hotels_router, prefix="/api/v1")
app.include_router(rooms_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(bookings_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")

if __name__ == "__main__":
    print("=" * 50)
    print("Hotel Booking API Starting...")
    print("URL: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Health: http://localhost:8000/health")
    print("RabbitMQ: http://localhost:15672 (guest/guest)")
    print("Redis: localhost:6379")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False  
    )