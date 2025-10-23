import logging
from app.schemas.messages import NotificationMessage, NotificationType
from app.core.rabbitmq import get_rabbitmq_manager

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.rabbitmq_manager = None
    
    async def _get_manager(self):
        if not self.rabbitmq_manager:
            self.rabbitmq_manager = await get_rabbitmq_manager()
        return self.rabbitmq_manager
    
    async def send_booking_confirmation(self, user_email: str, user_name: str, booking_data: dict):
        """Отправить подтверждение бронирования"""
        message = NotificationMessage(
            notification_type=NotificationType.EMAIL,
            recipient=user_email,
            subject="Подтверждение бронирования",
            message=f"""
                Уважаемый(ая) {user_name},

                Ваше бронирование подтверждено!

                Детали бронирования:
                - Номер бронирования: {booking_data.get('booking_reference')}
                - Отель: {booking_data.get('hotel_name', 'Название отеля')}
                - Комната: {booking_data.get('room_number')}
                - Заезд: {booking_data['check_in_date'].strftime('%d.%m.%Y %H:%M')}
                - Выезд: {booking_data['check_out_date'].strftime('%d.%m.%Y %H:%M')}
                - Стоимость: {booking_data['total_price']} руб.

                Спасибо за выбор нашего сервиса!
            """.strip(),
            template_id="booking_confirmation"
        )
        
        manager = await self._get_manager()
        await manager.publish_message(
            exchange="notification_events",
            routing_key="",
            message=message.dict()
        )
        logger.info(f"Booking confirmation sent to {user_email}")
    
    async def send_booking_cancellation(self, user_email: str, user_name: str, booking_data: dict):
        """Отправить уведомление об отмене бронирования"""
        message = NotificationMessage(
            notification_type=NotificationType.EMAIL,
            recipient=user_email,
            subject="Отмена бронирования",
            message=f"""
                Уважаемый(ая) {user_name},

                Ваше бронирование №{booking_data.get('booking_reference')} было отменено.

                Если у вас есть вопросы, свяжитесь с нашей службой поддержки.

                С уважением,
                Команда Hotel Booking
            """.strip()
        )
        
        manager = await self._get_manager()
        await manager.publish_message(
            exchange="notification_events",
            routing_key="",
            message=message.dict()
        )