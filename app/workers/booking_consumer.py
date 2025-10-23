import asyncio
import aio_pika
import json
import logging
from typing import Callable

logger = logging.getLogger(__name__)

class BookingConsumer:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.channel = None
    
    async def connect(self):
        """Подключиться к RabbitMQ"""
        self.connection = await aio_pika.connect_robust(self.connection_string)
        self.channel = await self.connection.channel()
        
        await self.channel.set_qos(prefetch_count=1)
        
        logger.info("Booking consumer connected to RabbitMQ")
    
    async def consume_booking_events(self, callback: Callable):
        """Потреблять события бронирований"""
        exchange = await self.channel.declare_exchange(
            "booking_events", 
            aio_pika.ExchangeType.TOPIC,
            durable=True
        )
        
        queue = await self.channel.declare_queue(
            "booking_events_queue",
            durable=True
        )
        
        await queue.bind(exchange, routing_key="booking.created")
        await queue.bind(exchange, routing_key="booking.updated")
        await queue.bind(exchange, routing_key="booking.cancelled")
        await queue.bind(exchange, routing_key="booking.checked_in")
        await queue.bind(exchange, routing_key="booking.checked_out")
        
        logger.info("Starting to consume booking events...")
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    try:
                        body = json.loads(message.body.decode())
                        await callback(body)
                        logger.info(f"Processed booking event: {body.get('event_type')}")
                    except Exception as e:
                        logger.error(f"Error processing message: {e}")
    
    async def close(self):
        """Закрыть соединение"""
        if self.connection:
            await self.connection.close()