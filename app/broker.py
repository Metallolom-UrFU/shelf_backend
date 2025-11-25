"""Dramatiq broker configuration for RabbitMQ"""
import dramatiq
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.results import Results
from dramatiq.results.backends import StubBackend

from .settings import settings

rabbitmq_broker = RabbitmqBroker(
    url=settings.rabbit.get_broker_url(),
    max_priority=10,
    confirm_delivery=True
)


rabbitmq_broker.add_middleware(Results(backend=StubBackend()))
dramatiq.set_broker(rabbitmq_broker)

rabbitmq_broker.declare_queue("default")
