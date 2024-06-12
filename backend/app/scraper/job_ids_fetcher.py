import requests
import time
import random
import os
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
import pika

from app.scraper.rabbit_mq_handler import RabbitMQHandler
from app.scraper.query_builder import QueryBuilder
from app.models import (
    ExperienceLevelsEnum,
    RemoteModalitiesEnum,
    SalaryRangeFiltersEnum,
    TimeFiltersEnum,
)
from app.logger import Logger
from app.core.db import engine


class JobIdsFetcher:
    """
    Main orchestrator class that will handle obtaining the job postings, writing them to the database, and adding the job query results to the database.
    """

    def __init__(
        self,
        jobs_base_url: str = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
        log_file_name: str = "scraper.log",
        rabbitmq_queue_name: str = "job_ids",
        job_ids_fetch_workers: int = 50,
        max_wait_time: int = 75,
        max_retries: int = 30,
        ids_per_request: int = 10,
    ):
        self.job_ids_fetch_workers = job_ids_fetch_workers
        self.max_wait_time = max_wait_time
        self.max_retries = max_retries
        self.ids_per_request = ids_per_request
        self.logger = Logger(
            prefix="Orchestrator", log_file_name=log_file_name
        ).get_logger()
        self.query_builder = QueryBuilder(base_url=jobs_base_url)

        # RabiitMQ connection
        self.rabbitmq_queue_name = rabbitmq_queue_name
        self.rabbitmq_handler = RabbitMQHandler(log_file_name=log_file_name)

    def enqueue_job_id(self, job_id):
        self.rabbitmq_handler.publish_message(job_id, self.rabbitmq_queue_name)

    def perform_request(self, url):
        retry_count = 0
        while retry_count < self.max_retries:
            job_request = requests.get(url)
            if job_request.status_code == 200:
                return job_request
            if job_request.status_code == 429:
                self.logger.info("Too many requests, waiting before retrying...")
                time.sleep(random.randint(1, self.max_wait_time))
                retry_count += 1
                continue
        self.logger.error(f"Failed to extract data for url: {url}")
        return None

    def get_job_ids(self, url):
        request = self.perform_request(url)
        if request is None:
            return []
        list_data = request.text
        list_soup = BeautifulSoup(list_data, "html.parser")
        page_jobs = list_soup.find_all("li")
        job_id_list = [
            job.find("div", class_="base-card")["data-entity-urn"].split(":")[-1]
            for job in page_jobs
            if job.find("div", class_="base-card")
        ]
        self.logger.info(f"Extracted {len(job_id_list)} job ids")

        return job_id_list

    def get_job_ids_with_check(self, url, start):
        # This method fetches job IDs and checks their count
        partial_url = url + f"&start={start}"
        job_ids = self.get_job_ids(partial_url)
        return job_ids, len(job_ids) < self.ids_per_request

    def fetch_job_ids_in_parallel(self, base_url, batch_start):
        # This method is responsible for fetching job IDs in parallel
        with ThreadPoolExecutor(max_workers=self.job_ids_fetch_workers) as executor:
            # Prepare futures for parallel execution
            futures = [
                executor.submit(
                    self.get_job_ids_with_check,
                    base_url,
                    batch_num * self.ids_per_request,
                )
                for batch_num in range(
                    batch_start, batch_start + self.job_ids_fetch_workers
                )
            ]
            job_results = []
            flag_results = []

            for future in as_completed(futures):
                job_ids, is_last_batch = future.result()
                job_results.append(job_ids)
                flag_results.append(is_last_batch)
            return job_results, any(flag_results)

    def run_scraping_job(
        self,
        keywords: str | None = None,
        location: str | None = None,
        salary_range: SalaryRangeFiltersEnum | None = None,
        time_filter: TimeFiltersEnum | None = None,
        experience_level: ExperienceLevelsEnum | None = None,
        remote_modality: RemoteModalitiesEnum | None = None,
        company_id: int | None = None,
    ):
        if keywords:
            self.query_builder.add_keyword(keywords)
        if location:
            self.query_builder.add_location(location)
        if salary_range:
            self.query_builder.add_salary_range(salary_range)
        if time_filter:
            self.query_builder.add_time_filter(time_filter)
        if experience_level:
            self.query_builder.add_experience_level(experience_level)
        if remote_modality:
            self.query_builder.add_remote_modality(remote_modality)
        if company_id:
            self.query_builder.add_company_id(company_id)

        url = self.query_builder.build_url_and_write_to_db()
        batch_start = 0
        job_ids = []
        # We fetch all the possible job_ids
        while True:
            fetched_ids, process_should_stop_flag = self.fetch_job_ids_in_parallel(
                url, batch_start=batch_start
            )

            self.logger.info(fetched_ids)
            self.logger.info(process_should_stop_flag)
            self.logger.info(f"Batch start: {batch_start}")
            job_ids.extend(list(itertools.chain(*fetched_ids)))
            if process_should_stop_flag:
                break
            batch_start += self.job_ids_fetch_workers
        job_ids = list(set(job_ids))
        for job_id in job_ids:
            self.enqueue_job_id(job_id)


if __name__ == "__main__":
    job_keywords = [
        "Machine Learning Engineer",
        "Data Scientist",
        "AI Researcher",
        "Data Engineer",
        "Research Scientist",
        "Deep Learning Engineer",
        "NLP Engineer",
        "Computer Vision Engineer",
        "Artificial Intelligence Specialist",
        "Predictive Modeler",
        "Applied Scientist",
        "Data Analyst",
        "Machine Learning Researcher",
        "Big Data Engineer",
        "Reinforcement Learning Engineer",
        "Data Science Consultant",
        "Machine Learning Developer",
    ]

    for job_keyword in job_keywords:
        job_ids_fetcher = JobIdsFetcher()
        job_ids_fetcher.run_scraping_job(
            keywords=job_keyword,
            location="United States",
            # salary_range=SalaryRangeFiltersEnum.RANGE_160K_PLUS,
            # time_filter=TimeFiltersEnum.PAST_WEEK,
            # remote_modality=RemoteModalitiesEnum.REMOTE,
        )
