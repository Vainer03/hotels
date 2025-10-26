import logging
from typing import Optional, List, Dict, Any
from app.core.redis import get_redis_manager
from app.core.redis import RedisManager
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class CacheService:
    def __init__(self):
        self.redis_manager: Optional[RedisManager] = None
    
    async def _get_manager(self):
        if not self.redis_manager:
            self.redis_manager = await get_redis_manager()
        return self.redis_manager
    
    async def cache_hotel(self, hotel_id: int, hotel_data: Dict[str, Any], expire: int = 3600):
        """Кэшировать данные отеля"""
        manager = await self._get_manager()
        key = f"hotel:{hotel_id}"
        await manager.set_key(key, hotel_data, expire)
        logger.info(f"Hotel {hotel_id} cached")
    
    async def get_cached_hotel(self, hotel_id: int) -> Optional[Dict[str, Any]]:
        """Получить кэшированные данные отеля"""
        manager = await self._get_manager()
        key = f"hotel:{hotel_id}"
        return await manager.get_key(key)
    
    async def cache_available_rooms(self, search_params: Dict[str, Any], rooms_data: List[Dict[str, Any]], expire: int = 1800):
        """Кэшировать результаты поиска комнат"""
        manager = await self._get_manager()
        
        key_parts = [f"{k}:{v}" for k, v in sorted(search_params.items())]
        key = f"rooms_search:{':'.join(key_parts)}"
        
        await manager.set_key(key, rooms_data, expire)
        logger.info(f"Rooms search cached for key: {key}")
    
    async def get_cached_rooms(self, search_params: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Получить кэшированные результаты поиска комнат"""
        manager = await self._get_manager()
        
        key_parts = [f"{k}:{v}" for k, v in sorted(search_params.items())]
        key = f"rooms_search:{':'.join(key_parts)}"
        
        return await manager.get_key(key)
    
    # async def cache_user_bookings(self, user_id: int, bookings_data: List[Dict[str, Any]], expire: int = 1800):
    #     """Кэшировать бронирования пользователя"""
    #     manager = await self._get_manager()
    #     key = f"user_bookings:{user_id}"
    #     await manager.set_key(key, bookings_data, expire)
    #     logger.info(f"User {user_id} bookings cached")
    
    # async def get_cached_user_bookings(self, user_id: int) -> Optional[List[Dict[str, Any]]]:
    #     """Получить кэшированные бронирования пользователя"""
    #     manager = await self._get_manager()
    #     key = f"user_bookings:{user_id}"
    #     return await manager.get_key(key)

    async def cache_user_bookings(self, user_id: int, bookings_data: List[dict]):
        """Кэшировать бронирования пользователя"""
        try:
            manager = await self._get_manager()
            cache_key = f"user_bookings:{user_id}"
            await manager.set_key(cache_key, bookings_data, expire=300)
        except Exception as e:
            print(f"Cache error in cache_user_bookings: {e}")

    async def get_cached_user_bookings(self, user_id: int) -> Optional[List[dict]]:
        """Получить кэшированные бронирования пользователя"""
        try:
            manager = await self._get_manager()
            cache_key = f"user_bookings:{user_id}"
            return await manager.get_key(cache_key)
        except Exception as e:
            print(f"Cache error in get_cached_user_bookings: {e}")
            return None
    
    async def cache_booking_details(self, booking_id: int, booking_data: Dict[str, Any], expire: int = 3600):
        """Кэшировать детали бронирования"""
        manager = await self._get_manager()
        key = f"booking:{booking_id}"
        await manager.set_key(key, booking_data, expire)
        logger.info(f"Booking {booking_id} cached")
    
    async def get_cached_booking_details(self, booking_id: int) -> Optional[Dict[str, Any]]:
        """Получить кэшированные детали бронирования"""
        manager = await self._get_manager()
        key = f"booking:{booking_id}"
        return await manager.get_key(key)
    
    async def invalidate_hotel_cache(self, hotel_id: int):
        """Инвалидировать кэш отеля"""
        manager = await self._get_manager()
        
        await manager.delete_key(f"hotel:{hotel_id}")
        
        pattern = f"rooms_search:*hotel_id:{hotel_id}*"
        keys = await manager.keys(pattern)
        for key in keys:
            await manager.delete_key(key)
        
        logger.info(f"Cache invalidated for hotel {hotel_id}")
    
    async def invalidate_user_cache(self, user_id: int):
        """Инвалидировать кэш пользователя"""
        manager = await self._get_manager()
        
        await manager.delete_key(f"user_bookings:{user_id}")
        
        logger.info(f"Cache invalidated for user {user_id}")
    
    async def invalidate_booking_cache(self, booking_id: int):
        """Инвалидировать кэш бронирования"""
        manager = await self._get_manager()
        await manager.delete_key(f"booking:{booking_id}")
        logger.info(f"Cache invalidated for booking {booking_id}")
    
    async def track_booking_stats(self, hotel_id: int, room_id: int):
        """Трекинг статистики бронирований"""
        manager = await self._get_manager()
        
        await manager.increment(f"stats:hotel:{hotel_id}:bookings")
        await manager.increment(f"stats:room:{room_id}:bookings")
        await manager.increment("stats:total_bookings")
        
        await manager.add_to_set("popular:rooms", str(room_id))
        await manager.add_to_set("popular:hotels", str(hotel_id))
    
    async def get_booking_stats(self) -> Dict[str, Any]:
        """Получить статистику бронирований"""
        manager = await self._get_manager()
        
        total_bookings = await manager.get_key("stats:total_bookings") or 0
        popular_rooms = await manager.get_set("popular:rooms")
        popular_hotels = await manager.get_set("popular:hotels")
        
        return {
            "total_bookings": total_bookings,
            "popular_rooms": list(popular_rooms)[:10],
            "popular_hotels": list(popular_hotels)[:10]
        }
    
class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def set_cache(self, key, value, expire=3600):
    try:
        serialized_value = json.dumps(value, cls=JSONEncoder)
        self.redis_client.setex(key, expire, serialized_value)
    except Exception as e:
        print(f"Cache set error: {e}")