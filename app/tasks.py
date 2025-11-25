import time
from datetime import datetime

import dramatiq
from .broker import rabbitmq_broker



@dramatiq.actor
def example_task(name: str):
    """Example background task"""
    print(f"[{datetime.now()}] Example task started with name: {name}")
    time.sleep(2)
    print(f"[{datetime.now()}] Example task completed for: {name}")
    return f"Task completed for {name}"

