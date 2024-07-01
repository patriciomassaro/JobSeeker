import pika
import os
import time
from functools import wraps
from app.logger import Logger


class MaxRetriesExceededError(Exception):
    pass


def retry_on_connection_error(max_retries=5, delay=5):
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(self, *args, **kwargs)
                except (
                    pika.exceptions.AMQPConnectionError,
                    pika.exceptions.ChannelClosedByBroker,
                    pika.exceptions.StreamLostError,
                    ConnectionResetError,
                ) as e:
                    self.logger.error(
                        f"{func.__name__} failed: {e}. Attempt {attempt + 1} of {max_retries}"
                    )
                    if attempt < max_retries - 1:
                        self.logger.info(f"Reconnecting in {delay} seconds...")
                        time.sleep(delay)
                        self.connect_to_rabbitmq()
                    else:
                        self.logger.error(f"Max retries reached for {func.__name__}")
                        raise MaxRetriesExceededError(
                            f"Failed to execute {func.__name__} after {max_retries} attempts"
                        )
            return None

        return wrapper

    return decorator


class RabbitMQHandler:
    def __init__(self, log_file_name="rabbitmq.log", max_retries=5):
        self.logger = Logger(
            prefix="RabbitMQHandler", log_file_name=log_file_name
        ).get_logger()
        self.connection = None
        self.max_retries = max_retries
        self.reconnect_delay = 5
        self.max_reconnect_delay = 300
        self.connect_to_rabbitmq()

    @retry_on_connection_error()
    def connect_to_rabbitmq(self):
        if self.connection and not self.connection.is_closed:
            return

        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                port=int(os.getenv("RABBITMQ_PORT", "5672")),
                credentials=pika.PlainCredentials(
                    os.getenv("RABBITMQ_DEFAULT_USER", "guest"),
                    os.getenv("RABBITMQ_DEFAULT_PASS", "guest"),
                ),
                heartbeat=60,
                blocked_connection_timeout=300,
            )
        )
        self.channel = self.connection.channel()
        self.logger.info("Successfully connected to RabbitMQ")

    @retry_on_connection_error()
    def declare_queue(self, queue_name):
        self.channel.queue_declare(queue=queue_name)

    @retry_on_connection_error()
    def publish_message(self, message, queue_name):
        self.declare_queue(queue_name)
        self.channel.basic_publish(exchange="", routing_key=queue_name, body=message)
        self.logger.info(f"Published message to {queue_name}")

    @retry_on_connection_error()
    def fetch_message(self, queue_name):
        return self.channel.basic_get(queue=queue_name, auto_ack=False)

    @retry_on_connection_error()
    def acknowledge_message(self, delivery_tag):
        self.channel.basic_ack(delivery_tag=delivery_tag)

    def fetch_batch(self, queue_name, batch_size):
        messages = []
        delivery_tags = []

        for _ in range(batch_size):
            method_frame, header_frame, body = self.fetch_message(queue_name)
            if method_frame:
                messages.append(body.decode())
                delivery_tags.append(method_frame.delivery_tag)
            else:
                break

        return messages, delivery_tags

    def process_batch(
        self, queue_name, batch_size, process_func, error_queue_name=None
    ):
        messages, delivery_tags = self.fetch_batch(queue_name, batch_size)

        if not messages:
            return 0

        self.logger.info(f"Processing batch of {len(messages)} messages")

        try:
            process_func(messages)

            # Acknowledge all messages in the batch
            for tag in delivery_tags:
                self.acknowledge_message(tag)

            return len(messages)

        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            if error_queue_name:
                for message in messages:
                    try:
                        self.publish_message(message, error_queue_name)
                    except Exception as publish_error:
                        self.logger.error(
                            f"Failed to publish message to error queue: {publish_error}"
                        )

            # Acknowledge messages even if processing failed, to avoid redelivery
            for tag in delivery_tags:
                self.acknowledge_message(tag)

            return 0

    def start_consuming(
        self,
        queue_name,
        process_func,
        error_queue_name=None,
        batch_size=10,
        wait_time=0,
        check_interval=30,
    ):
        self.declare_queue(queue_name)
        if error_queue_name:
            self.declare_queue(error_queue_name)

        self.logger.info(f"Starting to consume messages from {queue_name}")

        while True:
            try:
                processed_count = self.process_batch(
                    queue_name, batch_size, process_func, error_queue_name
                )
                if processed_count == 0:
                    self.logger.info(
                        f"No messages in queue. Waiting for {check_interval} seconds."
                    )
                    time.sleep(check_interval)
                else:
                    self.logger.info(
                        f"Processed {processed_count} messages. Waiting for {wait_time} seconds before next batch."
                    )
                    time.sleep(wait_time)
            except MaxRetriesExceededError:
                self.logger.error("Max retries exceeded. Stopping consumer.")
                break
            except KeyboardInterrupt:
                self.logger.info("Interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                time.sleep(check_interval)

    def close_connection(self):
        if self.connection and self.connection.is_open:
            self.connection.close()
            self.logger.info("RabbitMQ connection closed")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_connection()
