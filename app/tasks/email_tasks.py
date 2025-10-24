import logging
from celery import shared_task
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, to_email: str, user_name: str, booking_data: dict):
    """Отправить email с подтверждением бронирования"""
    try:
        logger.info(f"Sending booking confirmation email to {to_email}")
        
        # Логика отправки email (заглушка для демонстрации)
        subject = f"Подтверждение бронирования №{booking_data.get('booking_reference', '')}"
        
        # Форматируем даты
        check_in = booking_data.get('check_in_date', '')
        check_out = booking_data.get('check_out_date', '')
        if isinstance(check_in, str):
            # Уже отформатировано
            pass
        else:
            # Предполагаем, что это datetime объект
            from datetime import datetime
            if hasattr(check_in, 'strftime'):
                check_in = check_in.strftime('%d.%m.%Y')
                check_out = check_out.strftime('%d.%m.%Y')
        
        message_body = f"""
Уважаемый(ая) {user_name},

Ваше бронирование подтверждено!

Детали бронирования:
- Номер бронирования: {booking_data.get('booking_reference', 'N/A')}
- Отель: {booking_data.get('hotel_name', 'Название отеля')}
- Комната: {booking_data.get('room_number', 'N/A')}
- Заезд: {check_in}
- Выезд: {check_out}
- Стоимость: {booking_data.get('total_price', 0)} руб.
- Количество гостей: {booking_data.get('number_of_guests', 1)}

Спасибо за выбор нашего сервиса!

С уважением,
Команда Hotel Booking
        """.strip()
        
        # В реальном приложении здесь был бы код отправки email
        # через SMTP, SendGrid, Mailgun и т.д.
        
        # Создаем сообщение (для демонстрации, без реальной отправки)
        msg = MIMEMultipart()
        msg['From'] = 'noreply@hotelbooking.com'
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(message_body, 'plain', 'utf-8'))
        
        logger.info(f"Email content prepared for {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Message: {message_body}")
        
        # Имитация отправки (в реальном приложении здесь был бы smtplib)
        time.sleep(2)
        
        logger.info(f"Email sent to {to_email}")
        
        return {
            "status": "success", 
            "email": to_email, 
            "booking_id": booking_data.get('id'),
            "message": "Email отправлен успешно"
        }
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        # Повторяем попытку через 60 секунд
        raise self.retry(countdown=60, exc=e)

@shared_task
def send_booking_cancellation_email(to_email: str, user_name: str, booking_data: dict):
    """Отправить email об отмене бронирования"""
    try:
        logger.info(f"Sending cancellation email to {to_email}")
        
        subject = f"Отмена бронирования №{booking_data.get('booking_reference', '')}"
        message_body = f"""
Уважаемый(ая) {user_name},

Ваше бронирование №{booking_data.get('booking_reference')} было отменено.

Детали отмененного бронирования:
- Отель: {booking_data.get('hotel_name', 'Название отеля')}
- Комната: {booking_data.get('room_number')}
- Заезд: {booking_data.get('check_in_date')}
- Выезд: {booking_data.get('check_out_date')}

Если отмена произошла по ошибке или у вас есть вопросы, 
свяжитесь с нашей службой поддержки.

С уважением,
Команда Hotel Booking
        """.strip()
        
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = 'noreply@hotelbooking.com'
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_body, 'plain', 'utf-8'))
        
        time.sleep(1)
        logger.info(f"Cancellation email sent to {to_email}")
        
        return {"status": "success", "email": to_email}
        
    except Exception as e:
        logger.error(f"Failed to send cancellation email: {e}")
        return {"status": "error", "error": str(e)}

@shared_task
def send_reminder_email(to_email: str, user_name: str, booking_data: dict, days_before: int):
    """Отправить напоминание о бронировании"""
    try:
        logger.info(f"Sending reminder email to {to_email} for {days_before} days before")
        
        subject = f"Напоминание о бронировании через {days_before} дней"
        message_body = f"""
Уважаемый(ая) {user_name},

Напоминаем о вашем предстоящем бронировании через {days_before} дней.

Детали бронирования:
- Номер бронирования: {booking_data.get('booking_reference')}
- Отель: {booking_data.get('hotel_name', 'Название отеля')}
- Адрес: {booking_data.get('hotel_address', 'Адрес отеля')}
- Заезд: {booking_data.get('check_in_date')}
- Выезд: {booking_data.get('check_out_date')}

Желаем приятного отдыха!

С уважением,
Команда Hotel Booking
        """.strip()
        
        # Создаем сообщение
        msg = MIMEMultipart()
        msg['From'] = 'noreply@hotelbooking.com'
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_body, 'plain', 'utf-8'))
        
        time.sleep(1)
        logger.info(f"Reminder email sent to {to_email}")
        
        return {"status": "success", "email": to_email, "days_before": days_before}
        
    except Exception as e:
        logger.error(f"Failed to send reminder email: {e}")
        return {"status": "error", "error": str(e)}