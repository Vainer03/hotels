from celery import Celery
import os

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "hotel_booking",
    broker=redis_url,
    backend=redis_url,
    include=[
        "tasks.email_tasks",
        "tasks.report_tasks", 
        "tasks.analytics_tasks"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tasks.email_tasks.*": {"queue": "emails"},
        "tasks.report_tasks.*": {"queue": "reports"},
        "tasks.analytics_tasks.*": {"queue": "analytics"},
    },
    task_annotations={
        "tasks.email_tasks.send_booking_confirmation_email": {"rate_limit": "10/m"},
        "tasks.report_tasks.generate_hotel_report": {"rate_limit": "2/m"},
    }
)