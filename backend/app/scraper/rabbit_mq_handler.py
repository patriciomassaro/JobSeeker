import pika
import os
import time
from app.logger import Logger


class RabbitMQHandler:
    def __init__(self, log_file_name="rabbitmq.log"):
        self.logger = Logger(
            prefix="RabbitMQHandler", log_file_name=log_file_name
        ).get_logger()
        self.connection_attempts = 0
        self.connect_to_rabbitmq()

    def connect_to_rabbitmq(self):
        while self.connection_attempts < 5:
            try:
                self.connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=os.getenv("RABBITMQ_HOST", "rabbitmq"),
                        port=os.getenv("RABBITMQ_PORT", "5672"),
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
                break
            except Exception as e:
                self.connection_attempts += 1
                self.logger.error(
                    f"Connection attempt {self.connection_attempts} failed: {e}"
                )
                time.sleep(5)  # Wait before retrying

    def declare_queue(self, queue_name):
        self.channel.queue_declare(queue=queue_name)

    def publish_message(self, message, queue_name):
        retries = 0
        try:
            self.channel.basic_publish(
                exchange="", routing_key=queue_name, body=message
            )
            self.logger.info(f"Published message to {queue_name}")
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            self.close_connection()
        except pika.exceptions.ConnectionClosed as e:
            retries += 1
            self.logger.error(f"Closed connection: {e}. Reconnecting...")
            self.connect_to_rabbitmq()
            if retries < 5:
                self.channel.basic_publish(
                    exchange="", routing_key=queue_name, body=message
                )
                self.logger.info(f"Published message to {queue_name}")
        except pika.exceptions.StreamLostError as e:
            retries += 1
            self.logger.error(f"Lost connection to RabbitMQ: {e}. Reconnecting...")
            self.connect_to_rabbitmq()
            if retries < 5:
                self.channel.basic_publish(
                    exchange="", routing_key=queue_name, body=message
                )
                self.logger.info(f"Published message to {queue_name}")

        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.close_connection()

    def close_connection(self):
        if self.connection.is_open:
            self.connection.close()
            self.logger.info("RabbitMQ connection closed")
