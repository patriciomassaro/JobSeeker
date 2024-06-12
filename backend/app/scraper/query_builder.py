from app.models import (
    TimeFiltersEnum,
    SalaryRangeFiltersEnum,
    RemoteModalitiesEnum,
    ExperienceLevelsEnum,
    JobPostingQueries,
)
from app.logger import Logger
from app.core.db import engine
from sqlmodel import Session


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
