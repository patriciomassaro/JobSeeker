import threading
import time
from app.scraper.extractors.company_extractor import CompanyExtractor
from app.logger import Logger
from app.scraper.rabbit_mq_handler import RabbitMQHandler

WAIT_TIME_BETWEEN_REQUESTS = 600


class CompanyQueueConsumer:
    def __init__(
        self,
        rabbitmq_queue_name="companies_to_scrape",
        error_queue_name="companies_to_scrape_errors",
        log_file_name="companies_consumer.log",
        batch_size=1,
        max_workers=1,
        check_interval=30,
    ):
        self.rabbitmq_handler = RabbitMQHandler(log_file_name=log_file_name)
        self.rabbitmq_queue_name = rabbitmq_queue_name
        self.error_queue_name = error_queue_name
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.check_interval = check_interval
        self.logger = Logger(
            prefix="CompaniesQueueConsumer", log_file_name=log_file_name
        ).get_logger()
        self.extractor = CompanyExtractor(
            log_file_name=log_file_name, wait_time=WAIT_TIME_BETWEEN_REQUESTS
        )
        self.companies_batch = []
        self.stop_event = threading.Event()
        self.rabbitmq_handler.declare_queue(self.rabbitmq_queue_name)
        self.rabbitmq_handler.declare_queue(self.error_queue_name)

    def publish_to_error_queue(self, companies):
        self.rabbitmq_handler.publish_message(companies, self.error_queue_name)

    def process_batch(self):
        if not self.companies_batch:
            return
        self.logger.info(f"Processing batch of {len(self.companies_batch)} job IDs")
        try:
            companies = self.extractor.process_companies_parallel(
                self.companies_batch, max_workers=self.max_workers
            )
        except Exception as e:
            self.logger.error(f"Error processing batch: {e}")
            for company in self.companies_batch:
                self.publish_to_error_queue(company)
        finally:
            self.companies_batch = []

    def callback(self, ch, method, properties, body):
        company = body.decode()
        self.logger.info(f"Received company: {company}")
        self.companies_batch.append(company)
        if len(self.companies_batch) >= self.batch_size:
            self.process_batch()

    def start_periodic_check(self):
        def check_batch():
            while not self.stop_event.is_set():
                time.sleep(self.check_interval)
                if self.companies_batch:
                    self.logger.info("Periodic check: processing remaining batch")
                    self.process_batch()

        threading.Thread(target=check_batch, daemon=True).start()

    def start_consuming(self):
        self.rabbitmq_handler.channel.basic_consume(
            queue=self.rabbitmq_queue_name,
            on_message_callback=self.callback,
            auto_ack=True,
        )
        self.logger.info("Starting to consume messages...")
        try:
            self.rabbitmq_handler.channel.start_consuming()
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
    consumer = CompanyQueueConsumer()
    consumer.start_consuming()
