from app.scraper.extractors.company_extractor import CompanyExtractor
from app.logger import Logger
from app.scraper.rabbit_mq_handler import RabbitMQHandler

WAIT_TIME_BETWEEN_REQUESTS = 300


class CompanyQueueConsumer:
    def __init__(
        self,
        rabbitmq_queue_name="companies_to_scrape",
        error_queue_name="companies_to_scrape_errors",
        log_file_name="companies_consumer.log",
        batch_size=10,
        max_workers=3,
        check_interval=30,
        max_retries=5,
    ):
        self.rabbitmq_handler = RabbitMQHandler(
            log_file_name=log_file_name, max_retries=max_retries
        )
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

    def process_companies(self, companies):
        self.extractor.process_companies_parallel(
            companies, max_workers=self.max_workers
        )

    def start_consuming(self):
        self.rabbitmq_handler.start_consuming(
            queue_name=self.rabbitmq_queue_name,
            process_func=self.process_companies,
            error_queue_name=self.error_queue_name,
            batch_size=self.batch_size,
            wait_time=WAIT_TIME_BETWEEN_REQUESTS,
            check_interval=self.check_interval,
        )


if __name__ == "__main__":
    consumer = CompanyQueueConsumer(
        batch_size=10, max_workers=1, check_interval=30, max_retries=5
    )
    consumer.start_consuming()
