import threading
import pika
import time
from app.core.db import engine
from app.scraper.extractors.job_postings_extractor import JobPostingDataExtractor
from app.logger import Logger
from app.models import JobPostings
from app.scraper.rabbit_mq_handler import RabbitMQHandler
from sqlmodel import Session, select


class JobQueueConsumer:
    def __init__(
        self,
        rabbitmq_queue_name="job_ids",
        error_queue_name="job_errors",
        log_file_name="consumer.log",
        batch_size=100,
        max_workers=20,
        check_interval=5,
    ):
        self.rabbitmq_handler = RabbitMQHandler(log_file_name=log_file_name)
        self.rabbitmq_queue_name = rabbitmq_queue_name
        self.error_queue_name = error_queue_name
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.check_interval = check_interval
        self.logger = Logger(
            prefix="JobQueueConsumer", log_file_name=log_file_name
        ).get_logger()
        self.extractor = JobPostingDataExtractor(log_file_name=log_file_name)
        self.job_id_batch = []
        self.stop_event = threading.Event()
        self.rabbitmq_handler.declare_queue(self.rabbitmq_queue_name)
        self.rabbitmq_handler.declare_queue(self.error_queue_name)
        self.channel = self.rabbitmq_handler.channel
        self.delivery_tags = []

    def publish_to_error_queue(self, job_id):
        self.rabbitmq_handler.publish_message(job_id, self.error_queue_name)

    def process_batch(self):
        if not self.job_id_batch:
            return
        self.logger.info(f"Processing batch of {len(self.job_id_batch)} job IDs")
        try:
            processed_ids = self.extractor.extract_job_postings(
                self.job_id_batch, max_workers=self.max_workers
            )
            for id in processed_ids:
                if id is None:
                    self.logger.error(f"Job ID {id} failed to process")
                    self.publish_to_error_queue(id)
                    continue
        finally:
            for tag in self.delivery_tags:
                try:
                    self.channel.basic_ack(delivery_tag=tag)
                except pika.exceptions.ChannelClosed as e:
                    self.logger.error(f"Channel closed: {e}")
                    self.rabbitmq_handler.connect_to_rabbitmq()
                    self.channel.basic_ack(delivery_tag=tag)

            self.job_id_batch = []
            self.delivery_tags = []

    def callback(self, ch, method, properties, body):
        job_id = body.decode()
        self.logger.info(f"Received job ID: {job_id}")
        self.job_id_batch.append(job_id)
        self.delivery_tags.append(method.delivery_tag)
        if len(self.job_id_batch) >= self.batch_size:
            self.process_batch()

    def start_periodic_check(self):
        def check_batch():
            while not self.stop_event.is_set():
                time.sleep(self.check_interval)
                if self.job_id_batch:
                    self.logger.info("Periodic check: processing remaining batch")
                    self.process_batch()

        threading.Thread(target=check_batch, daemon=True).start()

    def start_consuming(self):
        # Set prefetch count to batch_size to limit the number of messages sent before ack
        self.channel.basic_qos(prefetch_count=self.batch_size)
        self.channel.basic_consume(
            queue=self.rabbitmq_queue_name,
            on_message_callback=self.callback,
            auto_ack=False,
        )
        self.logger.info("Starting to consume messages...")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user")
            self.rabbitmq_handler.close_connection()
            self.process_batch()  # Process any remaining job IDs in the batch
        except pika.exceptions.ConnectionClosed as e:
            self.logger.error(f"Closed connection: {e}. Reconnecting...")
            self.process_batch()
            self.rabbitmq_handler.connect_to_rabbitmq()
            self.start_consuming()
        except pika.exceptions.StreamLostError as e:
            self.logger.error(f"Lost connection to RabbitMQ: {e}. Reconnecting...")
            self.process_batch()
            self.rabbitmq_handler.connect_to_rabbitmq()
            self.start_consuming()
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            self.rabbitmq_handler.close_connection()
            self.process_batch()  # Process any remaining job IDs in the batch


if __name__ == "__main__":
    consumer = JobQueueConsumer()
    consumer.start_consuming()
