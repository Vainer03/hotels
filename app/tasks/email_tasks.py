import logging
from celery import shared_task
from app.core.celery import celery_app
import time

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, user_email: str, user_name: str, booking_data: dict):
    """Отправить email с подтверждением бронирования"""
    try:
        logger.info(f"Sending booking confirmation email to {user_email}")
        
        subject = f"Подтверждение бронирования №{booking_data.get('booking_reference', '')}"
        message = f"""
Уважаемый(ая) {user_name},

Ваше бронирование подтверждено!

Детали бронирования:
- Номер бронирования: {booking_data.get('booking_reference')}
- Отель: {booking_data.get('hotel_name', 'Название отеля')}
- Комната: {booking_data.get('room_number')}
- Заезд: {booking_data['check_in_date']}
- Выезд: {booking_data['check_out_date']}
- Стоимость: {booking_data['total_price']} руб.
- Количество гостей: {booking_data.get('number_of_guests', 1)}

Спасибо за выбор нашего сервиса!

С уважением,
Команда Hotel Booking
        """.strip()
        
        logger.info(f"Email sent to {user_email}")
        
        time.sleep(1)
        
        return {"status": "success", "email": user_email, "booking_id": booking_data.get('id')}
        
    except Exception as e:
        logger.error(f"Failed to send email to {user_email}: {e}")
        raise self.retry(countdown=60, exc=e)

@shared_task
def send_booking_cancellation_email(user_email: str, user_name: str, booking_data: dict):
    """Отправить email об отмене бронирования"""
    try:
        logger.info(f"Sending cancellation email to {user_email}")
        
        subject = f"Отмена бронирования №{booking_data.get('booking_reference', '')}"
        message = f"""
Уважаемый(ая) {user_name},

Ваше бронирование №{booking_data.get('booking_reference')} было отменено.

Детали отмененного бронирования:
- Отель: {booking_data.get('hotel_name', 'Название отеля')}
- Комната: {booking_data.get('room_number')}
- Заезд: {booking_data['check_in_date']}
- Выезд: {booking_data['check_out_date']}

Если отмена произошла по ошибке или у вас есть вопросы, 
свяжитесь с нашей службой поддержки.

С уважением,
Команда Hotel Booking
        """.strip()
        
        time.sleep(1)
        logger.info(f"Cancellation email sent to {user_email}")
        
        return {"status": "success", "email": user_email}
        
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def send_reminder_email(user_email: str, user_name: str, booking_data: dict, days_before: int):
    """Отправить напоминание о бронировании"""
    try:
        logger.info(f"Sending reminder email to {user_email} for {days_before} days before")
        
        subject = f"Напоминание о бронировании через {days_before} дней"
        message = f"""
Уважаемый(ая) {user_name},

Напоминаем о вашем предстоящем бронировании через {days_before} дней.

Детали бронирования:
- Номер бронирования: {booking_data.get('booking_reference')}
- Отель: {booking_data.get('hotel_name', 'Название отеля')}
- Адрес: {booking_data.get('hotel_address', 'Адрес отеля')}
- Заезд: {booking_data['check_in_date']}
- Выезд: {booking_data['check_out_date']}

Желаем приятного отдыха!

С уважением,
Команда Hotel Booking
        """.strip()
        
        time.sleep(1)
        logger.info(f"Reminder email sent to {user_email}")
        
        return {"status": "success", "email": user_email, "days_before": days_before}
        
    except Exception as e:
        logger.error(f"Failed to send reminder email: {e}")
        return {"status": "error", "error": str(e)}