import redis.asyncio as redis
import json
import logging
import os
from typing import Any, Optional, List, Dict

logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis: Optional[redis.Redis] = None
    
    async def connect(self):
        """Подключиться к Redis"""
        try:
            logger.info(f"Connecting to Redis at {self.redis_url}")
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Continuing without Redis...")
    
    async def close(self):
        """Закрыть соединение с Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def set_key(self, key: str, value: Any, expire: int = 3600):
        """Установить ключ со значением"""
        try:
            if not self.redis:
                return
            serialized_value = json.dumps(value)
            await self.redis.set(key, serialized_value, ex=expire)
        except Exception as e:
            logger.error(f"Failed to set key {key}: {e}")
    
    async def get_key(self, key: str) -> Optional[Any]:
        """Получить значение по ключу"""
        try:
            if not self.redis:
                return None
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Failed to get key {key}: {e}")
            return None
    
    async def delete_key(self, key: str):
        """Удалить ключ"""
        try:
            if not self.redis:
                return
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Failed to delete key {key}: {e}")
    
    async def keys(self, pattern: str) -> List[str]:
        """Найти ключи по шаблону"""
        try:
            if not self.redis:
                return []
            return await self.redis.keys(pattern)
        except Exception as e:
            logger.error(f"Failed to get keys for pattern {pattern}: {e}")
            return []
    
    async def increment(self, key: str) -> int:
        """Инкрементировать значение"""
        try:
            if not self.redis:
                return 0
            return await self.redis.incr(key)
        except Exception as e:
            logger.error(f"Failed to increment key {key}: {e}")
            return 0
    
    async def add_to_set(self, key: str, value: str):
        """Добавить значение в множество"""
        try:
            if not self.redis:
                return
            await self.redis.sadd(key, value)
        except Exception as e:
            logger.error(f"Failed to add to set {key}: {e}")
    
    async def get_set(self, key: str) -> set:
        """Получить множество"""
        try:
            if not self.redis:
                return set()
            return await self.redis.smembers(key)
        except Exception as e:
            logger.error(f"Failed to get set {key}: {e}")
            return set()

redis_manager: Optional[RedisManager] = None

async def get_redis_manager() -> RedisManager:
    """Dependency для получения менеджера Redis"""
    global redis_manager
    if redis_manager is None:
        redis_manager = RedisManager()
        await redis_manager.connect()
    return redis_manager