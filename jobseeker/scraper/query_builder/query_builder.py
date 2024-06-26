from jobseeker.scraper.query_builder.filters import FilterRemoteModality, FilterSalaryRange, FilterTime, FilterExperienceLevel,build_company_search_url
from jobseeker.database.models import JobQuery as JobQueryDBModel
from jobseeker.scraper.datatypes import JobQuery
from jobseeker.logger import Logger
from jobseeker.database import DatabaseManager


def parse_input(query_parameter:str,
                input_str:str,):
    input_str = input_str.strip()
    input_str = input_str.lower()
    input_str = input_str.replace(" ","%20")
    return f"{query_parameter}={input_str}"


class QueryBuilder:
    def __init__(self, base_url: str):
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

    def add_company_id(self, company_id: int = None):
        if company_id is not None:
            self.params.append(f"f_C={company_id}")
            self.company_id = company_id
        else:
            self.params.append("")  # Add empty string for optional parameters
            self.company_id = None
        return self

    def add_salary_range(self, salary_range: FilterSalaryRange):
        self.params.append(salary_range.get_param(salary_range.value) if salary_range is not None else "")
        self.salary_range = salary_range.value
        return self

    def add_time_filter(self, time_filter: FilterTime):
        self.params.append(time_filter.get_param(time_filter.value))
        self.time_filter = time_filter.value
        return self

    def add_experience_level(self, experience_level: FilterExperienceLevel):
        self.params.append(experience_level.get_param(experience_level.value))
        self.experience_level = experience_level.value
        return self

    def add_remote_modality(self, remote_modality: FilterRemoteModality):
        self.params.append(remote_modality.get_param(remote_modality.value))
        self.remote_modality = remote_modality.value
        return self

    @staticmethod
    def format_input(query_parameter: str, input_str: str)-> str:
        input_str = input_str.strip().lower().replace(" ", "%20").replace(",", "%2C")
        return f"{query_parameter}={input_str}" if input_str else ""

    def write_query_to_database(self, query_url: str):
        database_manager=DatabaseManager()
        query=JobQuery(
            url=query_url,
            company_id=self.company_id if hasattr(self,"company_id") else None,
            keywords=self.keywords if hasattr(self,"keywords") else None,
            location=self.location if hasattr(self,"location") else None,
            salary_range_id=self.salary_range if hasattr(self,"salary_range") else None,
            time_filter_id=self.time_filter if hasattr(self,"time_filter") else None,
            experience_level_id=self.experience_level if hasattr(self,"experience_level") else None,
            remote_modality_id=self.remote_modality if hasattr(self,"remote_modality") else None
            )
        query_db_object = JobQueryDBModel(**query.to_dict())
        self.logger.info(f"Adding query to database")
        object_id = database_manager.add_object(query_db_object)
        # return the id of the query
        return object_id
        
    
    def build_url(self):
        # Filter out empty strings
        non_empty_params = filter(None, self.params)
        formatted_params = '?' + "&".join(non_empty_params)
        return self.base_url + formatted_params, self.write_query_to_database(self.base_url + formatted_params)


if __name__ == "__main__":
    # Example usage
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    query_builder = QueryBuilder(base_url)

    url = (query_builder.add_keyword("machine learning engineer")
        .add_location("Washington DC")
        .add_company_id(None)  # Optional, can be omitted
        .add_salary_range(FilterSalaryRange.RANGE_140K_PLUS)
        .add_time_filter(FilterTime.PAST_WEEK)
        .add_experience_level(FilterExperienceLevel.ANY_EXPERIENCE_LEVEL)
        .add_remote_modality(FilterRemoteModality.REMOTE)
        .build_url())