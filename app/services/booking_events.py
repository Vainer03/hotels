import logging
from app.schemas.messages import BookingEvent, BookingEventType
from app.core.rabbitmq import get_rabbitmq_manager

logger = logging.getLogger(__name__)

class BookingEventService:
    def __init__(self):
        self.rabbitmq_manager = None
    
    async def _get_manager(self):
        if not self.rabbitmq_manager:
            self.rabbitmq_manager = await get_rabbitmq_manager()
        return self.rabbitmq_manager
    
    async def publish_booking_created(self, booking_data: dict):
        """Опубликовать событие создания бронирования"""
        event = BookingEvent(
            event_type=BookingEventType.CREATED,
            booking_id=booking_data["id"],
            user_id=booking_data["user_id"],
            hotel_id=booking_data["hotel_id"],
            room_id=booking_data["room_id"],
            check_in_date=booking_data["check_in_date"].isoformat(),
            check_out_date=booking_data["check_out_date"].isoformat(),
            total_price=booking_data["total_price"],
            metadata={
                "booking_reference": booking_data.get("booking_reference"),
                "number_of_guests": booking_data.get("number_of_guests")
            }
        )
        
        manager = await self._get_manager()
        await manager.publish_message(
            exchange="booking_events",
            routing_key="booking.created",
            message=event.dict()
        )
        logger.info(f"Booking created event published for booking {booking_data['id']}")
    
    async def publish_booking_cancelled(self, booking_data: dict):
        """Опубликовать событие отмены бронирования"""
        event = BookingEvent(
            event_type=BookingEventType.CANCELLED,
            booking_id=booking_data["id"],
            user_id=booking_data["user_id"],
            hotel_id=booking_data["hotel_id"],
            room_id=booking_data["room_id"],
            check_in_date=booking_data["check_in_date"],
            check_out_date=booking_data["check_out_date"],
            total_price=booking_data["total_price"],
            metadata={
                "cancellation_reason": "user_cancelled"
            }
        )
        
        manager = await self._get_manager()
        await manager.publish_message(
            exchange="booking_events",
            routing_key="booking.cancelled",
            message=event.dict()
        )
        logger.info(f"Booking cancelled event published for booking {booking_data['id']}")
    
    async def publish_booking_checked_in(self, booking_data: dict):
        """Опубликовать событие заезда"""
        event = BookingEvent(
            event_type=BookingEventType.CHECKED_IN,
            booking_id=booking_data["id"],
            user_id=booking_data["user_id"],
            hotel_id=booking_data["hotel_id"],
            room_id=booking_data["room_id"],
            check_in_date=booking_data["check_in_date"],
            check_out_date=booking_data["check_out_date"],
            total_price=booking_data["total_price"]
        )
        
        manager = await self._get_manager()
        await manager.publish_message(
            exchange="booking_events",
            routing_key="booking.checked_in",
            message=event.dict()
        )