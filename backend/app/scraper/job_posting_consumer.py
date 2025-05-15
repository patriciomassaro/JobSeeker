from app.scraper.extractors.job_postings_extractor import JobPostingDataExtractor
from app.logger import Logger
from app.models import JobPostingsToScrape
from app.core.db import engine
from sqlmodel import Session, select


def get_job_ids_to_scrape() -> list[int]:
    with Session(engine) as session:
        statement = select(JobPostingsToScrape.linkedin_job_id).where(
            JobPostingsToScrape.processed == False
        )
        jobs_to_scrape = list(session.exec(statement).all())
        logger.info(f"Found {len(jobs_to_scrape)} jobs to scrape")
        return jobs_to_scrape


logger = Logger(
    prefix="JobQueueConsumer", log_file_name="job_consumer.log"
).get_logger()
max_workers = 20


def main():
    extractor = JobPostingDataExtractor(log_file_name="job_consumer.log")
    job_ids = get_job_ids_to_scrape()
    extractor.extract_job_postings(
        [str(job_id) for job_id in job_ids], max_workers=max_workers
    )


if __name__ == "__main__":
    main()
