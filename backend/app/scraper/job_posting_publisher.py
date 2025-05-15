import requests
import time
import random
from sqlmodel import Session
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools
from sqlalchemy.exc import IntegrityError

from app.models import (
    ExperienceLevelsEnum,
    RemoteModalitiesEnum,
    SalaryRangeFiltersEnum,
    TimeFiltersEnum,
    JobPostingQueries,
    JobPostingsToScrape,
)
from app.logger import Logger
from app.core.db import engine


def parse_input(
    query_parameter: str,
    input_str: str,
):
    input_str = input_str.strip()
    input_str = input_str.lower()
    input_str = input_str.replace(" ", "%20")
    return f"{query_parameter}={input_str}"


class QueryBuilder:
    def __init__(
        self,
        base_url: str = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search/",
    ):
        self.logger = Logger(prefix="QueryBuilder").get_logger()
        self.base_url = base_url
        self.params = []  # Store parameters without any prefix

    def add_keyword(self, keyword: str):
        self.params.append(self.format_input("keywords", keyword))
        self.keywords = keyword
        return self

    def add_location(self, location: str):
        self.params.append(self.format_input("location", location))
        self.location = location
        return self

    def add_company_id(self, company_id: int | None = None):
        if company_id is not None:
            self.params.append(f"f_C={company_id}")
            self.company_id = company_id
        else:
            self.params.append("")  # Add empty string for optional parameters
            self.company_id = None
        return self

    def add_salary_range(self, salary_range: SalaryRangeFiltersEnum):
        self.params.append(
            salary_range.get_query_param(salary_range.value, "f_SB2=", value_index=0)
            if salary_range is not None
            else ""
        )
        self.salary_range = salary_range.value[0]
        return self

    def add_time_filter(self, time_filter: TimeFiltersEnum):
        self.params.append(time_filter.get_query_param(time_filter.value, "f_TPR=r"))
        self.time_filter = time_filter.value[0]
        return self

    def add_experience_level(self, experience_level: ExperienceLevelsEnum):
        self.params.append(
            experience_level.get_query_param(
                experience_level.value, "f_E=", value_index=0
            )
        )
        self.experience_level = experience_level.value[0]
        return self

    def add_remote_modality(self, remote_modality: RemoteModalitiesEnum):
        self.params.append(
            remote_modality.get_query_param(
                remote_modality.value, "f_WT=", value_index=0
            )
        )
        self.remote_modality = remote_modality.value[0]
        return self

    @staticmethod
    def format_input(query_parameter: str, input_str: str) -> str:
        input_str = input_str.strip().lower().replace(" ", "%20").replace(",", "%2C")
        return f"{query_parameter}={input_str}" if input_str else ""

    def build_url_and_write_to_db(self):
        self.url = self.build_url()
        query = JobPostingQueries(
            url=self.url,
            linkedin_company_id=self.company_id
            if hasattr(self, "company_id")
            else None,
            keywords=self.keywords,
            location=self.location if hasattr(self, "location") else None,
            salary_range_id=self.salary_range
            if hasattr(self, "salary_range")
            else None,
            time_filter_id=self.time_filter if hasattr(self, "time_filter") else None,
            experience_level_id=self.experience_level
            if hasattr(self, "experience_level")
            else None,
            remote_modality_id=self.remote_modality
            if hasattr(self, "remote_modality")
            else None,
        )
        self.logger.info("Adding query to database")
        with Session(engine) as session:
            session.add(query)
            session.commit()
        return self.url

    def build_url(self) -> str:
        non_empty_params = filter(None, self.params)
        formatted_params = "?" + "&".join(non_empty_params)
        return self.base_url + formatted_params


class JobIdsFetcher:
    def __init__(
        self,
        jobs_base_url: str = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
        log_file_name: str = "scraper.log",
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

    def run_job_ids_to_db(self, job_ids: list[str]) -> None:
        with Session(engine) as session:
            for job_id in job_ids:
                try:
                    job_posting = JobPostingsToScrape(linkedin_job_id=int(job_id))
                    session.add(job_posting)
                    session.commit()
                except IntegrityError:
                    session.rollback()
                    print(f"Job ID {job_id} already exists in the database. Skipping.")

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
        self.run_job_ids_to_db(job_ids)

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

    job_ids_fetcher = JobIdsFetcher(job_ids_fetch_workers=10, max_wait_time=10)
    for job_keyword in job_keywords:
        job_ids_fetcher.run_scraping_job(
            keywords=job_keyword,
            location="Washington DC",
        )


if __name__ == "__main__":
    main()
