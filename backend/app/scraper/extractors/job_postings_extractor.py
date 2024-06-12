import requests
from bs4 import BeautifulSoup
from bs4.element import Tag

import random
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models import (
    JobPostings,
    SeniorityLevelsEnum,
    EmploymentTypesEnum,
)
from app.logger import Logger
from app.core.db import engine
from sqlmodel import Session

JOB_POSTING_BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"
MAXIMUM_RETRIES = 40
WAIT_TIME_BETWEEN_REQUESTS_LIMITS = (1, 30)


class JobPostingDataExtractor:
    def __init__(
        self,
        log_file_name: str = "scraper.log",
        job_url="https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/",
        job_posting_base_url: str = JOB_POSTING_BASE_URL,
        maximum_retries: int = MAXIMUM_RETRIES,
        wait_time_limits: tuple = WAIT_TIME_BETWEEN_REQUESTS_LIMITS,
    ):
        self.logger = Logger(
            prefix="JobPostingDataExtractor", log_file_name=log_file_name
        ).get_logger()
        self.job_posting_base_url = job_posting_base_url
        self.maximum_retries = maximum_retries
        self.wait_time_limits = wait_time_limits
        self.job_url = job_url

    @staticmethod
    def _extract_job_criteria_based_on_string(
        job_soup: BeautifulSoup, text: str
    ) -> str | None:
        # Iterate through each li element
        for li in job_soup.select(".description__job-criteria-item"):
            h3_tag = li.find("h3")
            if h3_tag and h3_tag.text.strip() == text:
                span_tag = li.find("span", class_="description__job-criteria-text")
                if span_tag:
                    return span_tag.text.strip()
        return None

    def _extract_seniority_level(self, job_soup: BeautifulSoup) -> int | None:
        seniority_level_string = self._extract_job_criteria_based_on_string(
            job_soup, "Seniority level"
        )
        # Get the id of the corresponding string in the enum
        seniority_level_id = None
        if seniority_level_string:
            seniority_level_id = SeniorityLevelsEnum.get_id(
                seniority_level_string.strip()
            )

        return seniority_level_id

    def _extract_employment_type(self, job_soup: BeautifulSoup) -> int | None:
        employment_type_str = self._extract_job_criteria_based_on_string(
            job_soup, "Employment type"
        )
        employment_type_id = None
        if employment_type_str:
            employment_type_id = EmploymentTypesEnum.get_id(employment_type_str.strip())
        return employment_type_id

    def _extract_job_functions(self, job_soup: BeautifulSoup) -> list:
        job_functions = self._extract_job_criteria_based_on_string(
            job_soup, "Job function"
        )
        if job_functions:
            job_functions = job_functions.replace("and", ",")
            return [
                job_function.strip().replace("and ", ",")
                for job_function in job_functions.split(",")
            ]
        return []

    def _extract_industries(self, job_soup: BeautifulSoup) -> list[str]:
        industries = self._extract_job_criteria_based_on_string(job_soup, "Industries")
        if industries:
            return [
                industry.strip().replace("and ", "")
                for industry in industries.split(",")
            ]
        return []

    @staticmethod
    def _extract_job_title(job_soup: BeautifulSoup) -> str:
        """
        Extracts the job title from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Job title text
        """
        job_title_tag = job_soup.find(
            "h2",
            {
                "class": "top-card-layout__title font-sans text-lg papabear:text-xl font-bold leading-open text-color-text mb-0 topcard__title"
            },
        )
        if job_title_tag:
            return job_title_tag.text.strip()
        return ""

    @staticmethod
    def _extract_company_name(job_soup: BeautifulSoup) -> str:
        """
        Extracts the company name from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Company name text
        """
        company_name = job_soup.find(
            "a", class_="topcard__org-name-link topcard__flavor--black-link"
        )

        if company_name:
            return company_name.text.strip()
        return ""

    def _extract_company_url(self, job_soup: BeautifulSoup) -> str | None:
        """
        Extracts the company URL from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Company URL text
        """
        company_url = job_soup.find(
            "a", class_="topcard__org-name-link topcard__flavor--black-link"
        )
        if company_url:
            return company_url["href"].split("?trk")[0]  # type: ignore
        return None

    @staticmethod
    def _extract_job_location(job_soup: BeautifulSoup) -> str | None:
        """
        Extracts the job location from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Job location text
        """
        job_location = job_soup.find(
            "span", class_="topcard__flavor topcard__flavor--bullet"
        )
        if job_location:
            return job_location.text.strip()
        return None

    @staticmethod
    def _extract_job_poster(job_soup: BeautifulSoup) -> dict | None:
        name = ""
        profile_url = ""
        message_recruiter_div = job_soup.find("div", class_="message-the-recruiter")
        if message_recruiter_div:
            # If the div exists, find the <a> tag for the URL and name
            profile_tag = message_recruiter_div.find(
                "a",
                class_="base-card__full-link absolute top-0 right-0 bottom-0 left-0 p-0 z-[2]",  # type: ignore we avoid using class because it overlaps with class
            )
            # Find the <h4> tag within the div for the detailed title
            detail_title_tag = message_recruiter_div.find(
                "h4",
                class_="base-main-card__subtitle body-text text-color-text overflow-hidden",  # type: ignore we avoid using class because it overlaps with class
            )

            if profile_tag and detail_title_tag:
                # Extract the name, which is also visually hidden but available for screen readers
                name_tag = profile_tag.find("span", class_="sr-only")  # type: ignore we avoid using class because it overlaps with class
                name = name_tag.text.strip() if name_tag else None
                # Extract the profile URL
                if isinstance(profile_tag, Tag):
                    profile_url = profile_tag.get("href", None)
                    if isinstance(profile_url, str):
                        profile_url = profile_url.split("?trk")[0]

                # Extract the title
                title = detail_title_tag.text.strip()
                # Compile the extracted information
                info = {"name": name, "title": title, "profile_url": profile_url}
                return info
        else:
            return None

    @staticmethod
    def _extract_salary_range(job_soup: BeautifulSoup) -> tuple | None:
        """
        Extracts the salary range from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Tuple of salary range (low, high)
        """
        salary_range = job_soup.find("div", class_="salary compensation__salary")
        if salary_range:
            # Extract the text and split it into low and high ranges
            salary_text = salary_range.get_text(separator=" ", strip=True)
            # Use regex to extract the numbers from the text
            matches = re.findall(r"\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?", salary_text)
            # if we found two matches, return them as a tuple
            if len(matches) == 2:
                return tuple(
                    int(float(salary.replace("$", "").replace(",", "")))
                    for salary in matches
                )
        return None

    @staticmethod
    def _extract_job_description(job_soup: BeautifulSoup) -> str:
        """
        Extracts and formats the job description from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Formatted job description text
        """
        formatted_text_pieces = []
        job_description_tag = job_soup.find(
            "div", {"class": "show-more-less-html__markup"}
        )
        # Extract and format <strong> elements and following siblings until the next <strong> element or list
        for child in job_description_tag.children:  # type: ignore
            if child.name == "strong":  # type: ignore
                # Format headings
                formatted_text_pieces.append(f"{child.get_text().strip()}\n")
            elif child.name == "p":  # type: ignore
                # Format paragraphs, handling <br> tags as new lines
                text = child.get_text(separator="\n", strip=True)
                formatted_text_pieces.append(text)
            elif child.name in ["ul", "ol"]:  # type: ignore
                # Format lists
                list_items = [
                    li.get_text(separator="\n", strip=True)
                    for li in child.find_all("li")  # type: ignore
                ]
                formatted_list = "\n".join([f"- {item}" for item in list_items])
                formatted_text_pieces.append(formatted_list)
            elif child.name == "br":  # type: ignore
                # Optionally, handle breaks if needed
                continue
            else:
                # Handle other types of elements as needed or ignore
                text = child.get_text(separator="\n", strip=True)
                if text:
                    formatted_text_pieces.append(text)

        # Join the formatted text pieces into a single string
        formatted_text = "\n\n".join(formatted_text_pieces)

        return formatted_text

    def _create_job_posting(self, job_id: str, job_soup: BeautifulSoup) -> int:
        job_poster_info = self._extract_job_poster(job_soup)
        salary_range = self._extract_salary_range(job_soup)

        # You might need to adjust this part based on how you're initializing JobPosting
        job_posting = JobPostings(
            linkedin_id=int(job_id),
            html=str(job_soup),
            title=self._extract_job_title(job_soup),
            location=self._extract_job_location(job_soup),
            seniority_level=self._extract_seniority_level(job_soup),
            employment_type=self._extract_employment_type(job_soup),
            description=self._extract_job_description(job_soup),
            company=self._extract_company_name(job_soup),
            company_url=self._extract_company_url(job_soup),
            job_salary_min=salary_range[0] if salary_range else None,
            job_salary_max=salary_range[1] if salary_range else None,
            job_poster_profile=job_poster_info.get("profile_url", None)
            if job_poster_info
            else None,
            job_poster_name=job_poster_info.get("name", None)
            if job_poster_info
            else None,
            job_functions=self._extract_job_functions(job_soup),
            industries=self._extract_industries(job_soup),
        )
        with Session(engine) as session:
            self.logger.info(f"{job_id} - Successfully extracted data")
            existing_posting = (
                session.query(JobPostings)
                .filter_by(linkedin_id=job_posting.linkedin_id)
                .first()
            )
            if existing_posting:
                # Update existing posting
                for key, value in job_posting.dict().items():
                    if key not in ["id", "linkedin_id"]:
                        setattr(existing_posting, key, value)
                session.add(existing_posting)
            else:
                # Insert new posting
                session.add(job_posting)
            session.commit()
            return job_posting.linkedin_id

    def extract_single_job_posting(self, job_id: str) -> int:
        job_url = self.job_posting_base_url + job_id
        self.logger.info(f"{job_id} - Scraping job")
        retries = 0
        while retries < self.maximum_retries:
            job_request = requests.get(job_url)
            if job_request.status_code == 429:
                wait_time = random.randint(*self.wait_time_limits)
                self.logger.info(
                    f"{job_id} - Too many requests, waiting {wait_time} secs..."
                )
                time.sleep(wait_time)
                retries += 1
                continue
            job_data = job_request.text
            job_soup = BeautifulSoup(job_data, "html.parser")
            return self._create_job_posting(job_id, job_soup)

        self.logger.error(
            f"{job_id} Failed to extract data after {self.maximum_retries} retries."
        )
        raise (Exception(f"Failed to extract data for job ID: {job_id}"))

    def extract_job_postings(self, job_ids: list[str], max_workers: int = 5) -> list:
        """
        Extracts data for multiple job postings in parallel.

        :param job_ids: A list of job ID strings.
        :param max_workers: Maximum number of threads to use.
        :return: A list of JobPosting objects (or None for failed extractions).
        """
        job_postings = []

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map each job ID to a future object
            future_to_job_id = {
                executor.submit(self.extract_single_job_posting, job_id): job_id
                for job_id in job_ids
            }

            for future in as_completed(future_to_job_id):
                job_id = future_to_job_id[future]
                try:
                    job_posting = future.result()
                    job_postings.append(job_posting)
                except Exception as exc:
                    print(f"Job ID {job_id} generated an exception: {exc}")
                    job_postings.append(None)

        return job_postings
