from app.scraper.extractors.job_postings_extractor import JobPostingDataExtractor
from app.logger import Logger
from app.scraper.rabbit_mq_handler import RabbitMQHandler


class JobQueueConsumer:
    def __init__(
        self,
        rabbitmq_queue_name="job_ids",
        error_queue_name="job_errors",
        log_file_name="job_consumer.log",
        batch_size=100,
        max_workers=20,
        check_interval=5,
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
            prefix="JobQueueConsumer", log_file_name=log_file_name
        ).get_logger()
        self.extractor = JobPostingDataExtractor(log_file_name=log_file_name)

    def process_jobs(self, job_ids):
        self.logger.info(f"Processing batch of {len(job_ids)} job IDs")
        processed_ids = self.extractor.extract_job_postings(
            job_ids, max_workers=self.max_workers
        )
        for id in processed_ids:
            if id is None:
                self.logger.error(f"Job ID {id} failed to process")
                raise Exception(f"Failed to process job ID: {id}")

    def start_consuming(self):
        self.rabbitmq_handler.start_consuming(
            queue_name=self.rabbitmq_queue_name,
            process_func=self.process_jobs,
            error_queue_name=self.error_queue_name,
            batch_size=self.batch_size,
            wait_time=0,  # No wait time between batches for job processing
            check_interval=self.check_interval,
        )


if __name__ == "__main__":
    consumer = JobQueueConsumer(
        batch_size=100, max_workers=20, check_interval=5, max_retries=5
    )
    consumer.start_consuming()
