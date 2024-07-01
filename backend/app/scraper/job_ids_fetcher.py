import requests
import time
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools

from app.scraper.rabbit_mq_handler import RabbitMQHandler
from app.scraper.query_builder import QueryBuilder
from app.models import (
    ExperienceLevelsEnum,
    RemoteModalitiesEnum,
    SalaryRangeFiltersEnum,
    TimeFiltersEnum,
)
from app.logger import Logger


class JobIdsFetcher:
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
            prefix="JobIdsFetcher", log_file_name=log_file_name
        ).get_logger()
        self.query_builder = QueryBuilder(base_url=jobs_base_url)
        self.rabbitmq_handler = RabbitMQHandler(log_file_name=log_file_name)
        self.rabbitmq_queue_name = rabbitmq_queue_name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.rabbitmq_handler.close_connection()

    def enqueue_job_id(self, job_id: str) -> None:
        self.rabbitmq_handler.publish_message(job_id, self.rabbitmq_queue_name)

    def perform_request(self, url: str) -> requests.Response | None:
        for retry in range(self.max_retries):
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if (
                    isinstance(e, requests.exceptions.HTTPError)
                    and e.response.status_code == 429
                ):
                    self.logger.info("Too many requests, waiting before retrying...")
                    time.sleep(random.randint(1, self.max_wait_time))
                else:
                    self.logger.error(f"Request failed: {e}")
                if retry == self.max_retries - 1:
                    self.logger.error(f"Max retries reached for url: {url}")
                    return None
        return None

    def extract_job_ids(self, html_content: str) -> list[str]:
        soup = BeautifulSoup(html_content, "html.parser")
        job_elements = soup.find_all("div", class_="base-card")
        job_ids = [
            job["data-entity-urn"].split(":")[-1]
            for job in job_elements
            if "data-entity-urn" in job.attrs
        ]
        self.logger.info(f"Extracted {len(job_ids)} job ids")
        return job_ids

    def get_job_ids(self, url: str) -> list[str]:
        response = self.perform_request(url)
        if response is None:
            return []
        return self.extract_job_ids(response.text)

    def get_job_ids_with_check(self, url: str, start: int) -> tuple[list[str], bool]:
        partial_url = f"{url}&start={start}"
        job_ids = self.get_job_ids(partial_url)
        return job_ids, len(job_ids) < self.ids_per_request

    def fetch_job_ids_in_parallel(
        self, base_url: str, batch_start: int
    ) -> tuple[list[list[str]], bool]:
        with ThreadPoolExecutor(max_workers=self.job_ids_fetch_workers) as executor:
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
            results = [future.result() for future in as_completed(futures)]
            job_results, flag_results = zip(*results)
            return list(job_results), any(flag_results)

    def run_scraping_job(
        self,
        keywords: str | None = None,
        location: str | None = None,
        salary_range: SalaryRangeFiltersEnum | None = None,
        time_filter: TimeFiltersEnum | None = None,
        experience_level: ExperienceLevelsEnum | None = None,
        remote_modality: RemoteModalitiesEnum | None = None,
        company_id: int | None = None,
    ) -> None:
        self.build_query(
            keywords,
            location,
            salary_range,
            time_filter,
            experience_level,
            remote_modality,
            company_id,
        )
        url = self.query_builder.build_url_and_write_to_db()
        job_ids = self.fetch_all_job_ids(url)
        self.enqueue_job_ids(job_ids)

    def build_query(
        self,
        keywords,
        location,
        salary_range,
        time_filter,
        experience_level,
        remote_modality,
        company_id,
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

    def fetch_all_job_ids(self, url: str) -> list[str]:
        batch_start = 0
        all_job_ids = []
        while True:
            fetched_ids, process_should_stop = self.fetch_job_ids_in_parallel(
                url, batch_start
            )
            all_job_ids.extend(list(itertools.chain(*fetched_ids)))
            if process_should_stop:
                break
            batch_start += self.job_ids_fetch_workers
        return list(set(all_job_ids))

    def enqueue_job_ids(self, job_ids: list[str]) -> None:
        for job_id in job_ids:
            self.enqueue_job_id(job_id)


def main():
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

    with JobIdsFetcher(job_ids_fetch_workers=20) as job_ids_fetcher:
        for job_keyword in job_keywords:
            job_ids_fetcher.run_scraping_job(
                keywords=job_keyword,
                location="United States",
            )


if __name__ == "__main__":
    main()
