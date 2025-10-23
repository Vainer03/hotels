import aio_pika
import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class RabbitMQManager:
    def __init__(self, connection_string: str = None):
        self.connection_string = connection_string or os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
    
    async def connect(self):
        """Установить соединение с RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {self.connection_string}")
            self.connection = await aio_pika.connect_robust(self.connection_string)
            self.channel = await self.connection.channel()
            
            await self.channel.declare_exchange("booking_events", aio_pika.ExchangeType.TOPIC, durable=True)
            await self.channel.declare_exchange("notification_events", aio_pika.ExchangeType.FANOUT, durable=True)
            
            logger.info("Successfully connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            logger.warning("Continuing without RabbitMQ...")
    
    async def close(self):
        """Закрыть соединение с RabbitMQ"""
        if self.connection:
            await self.connection.close()
            logger.info("RabbitMQ connection closed")
    
    async def publish_message(self, exchange: str, routing_key: str, message: Dict[str, Any]):
        """Опубликовать сообщение в RabbitMQ"""
        try:
            if not self.channel:
                await self.connect()
            
            if not self.channel:  
                logger.warning("No RabbitMQ channel available, skipping message publish")
                return
            
            exchange_obj = await self.channel.get_exchange(exchange)
            message_body = json.dumps(message).encode()
            
            await exchange_obj.publish(
                aio_pika.Message(
                    body=message_body,
                    content_type="application/json",
                    delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                ),
                routing_key=routing_key
            )
            logger.info(f"Message published to {exchange} with routing key {routing_key}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")

rabbitmq_manager: Optional[RabbitMQManager] = None

async def get_rabbitmq_manager() -> RabbitMQManager:
    """Dependency для получения менеджера RabbitMQ"""
    global rabbitmq_manager
    if rabbitmq_manager is None:
        rabbitmq_manager = RabbitMQManager()
        await rabbitmq_manager.connect()
    return rabbitmq_manager