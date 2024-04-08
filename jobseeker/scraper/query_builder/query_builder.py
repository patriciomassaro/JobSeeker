import requests
from bs4 import BeautifulSoup
from bs4.element import Tag,ResultSet
import random
import pandas as pd
import time
import re
from datatypes import JobPosting
from typing import List
from enum import Enum
from dataclasses import dataclass




class FilterEnum(Enum):
    # This method can now be used by any Enum inheriting from ParamEnum
    @classmethod
    def get_param(cls,value, param_name):
        for item in cls:
            if item.value == value:
                return f"{param_name}={item.value}" if item.value is not None else ""
        return ""


class FilterTime(FilterEnum):
    PAST_24_HOURS = 'r86400'
    PAST_WEEK = 'r604800'
    PAST_MONTH = 'r2592000'
    ANY_TIME = None
    
    # Specific implementation for TimeFilter
    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_TPR")

class FilterSalaryRange(FilterEnum):
    RANGE_40K_PLUS = 1
    RANGE_60K_PLUS = 2
    RANGE_80K_PLUS = 3
    RANGE_100K_PLUS = 4
    RANGE_120K_PLUS = 5
    RANGE_140K_PLUS = 6
    RANGE_160K_PLUS = 7
    RANGE_180K_PLUS = 8
    RANGE_200K_PLUS = 9
    RANGE_ANY = None

    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_SB2")

class FilterExperienceLevel(FilterEnum):
    INTERNSHIP = 1
    ENTRY_LEVEL = 2
    ASSOCIATE = 3
    MID_SENIOR_LEVEL = 4
    DIRECTOR = 5
    EXECUTIVE = 6
    ANY_EXPERIENCE_LEVEL = None

    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_E")

def build_company_search_url(company_id:int = None):
    return f"f_C={company_id}" if company_id is not None else ""

class FilterRemoteModality(FilterEnum):
    ON_SITE = 1
    REMOTE = 2
    HYBRID =3
    ANY_MODALITY = None

    @classmethod
    def get_param(cls, value):
        return super().get_param(value, "f_WT")


def parse_input(query_parameter:str,
                input_str:str,):
    input_str = input_str.strip()
    input_str = input_str.lower()
    input_str = input_str.replace(" ","%20")
    return f"{query_parameter}={input_str}"


class QueryBuilder:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.params = []  # Store parameters without any prefix

    def add_keyword(self, keyword: str):
        self.params.append(self.format_input("keywords", keyword))
        return self

    def add_location(self, location: str):
        self.params.append(self.format_input("location", location))
        return self

    def add_company_id(self, company_id: int = None):
        if company_id is not None:
            self.params.append(f"f_C={company_id}")
        else:
            self.params.append("")  # Add empty string for optional parameters
        return self

    def add_salary_range(self, salary_range: FilterSalaryRange):
        self.params.append(salary_range.get_param(salary_range.value) if salary_range is not None else "")
        return self

    def add_time_filter(self, time_filter: FilterTime):
        self.params.append(time_filter.get_param(time_filter.value))
        return self

    def add_experience_level(self, experience_level: FilterExperienceLevel):
        self.params.append(experience_level.get_param(experience_level.value))
        return self

    def add_remote_modality(self, remote_modality: FilterRemoteModality):
        self.params.append(remote_modality.get_param(remote_modality.value))
        return self

    @staticmethod
    def format_input(query_parameter: str, input_str: str):
        input_str = input_str.strip().lower().replace(" ", "%20").replace(",", "%2C")
        return f"{query_parameter}={input_str}" if input_str else ""

    def build_url(self):
        # Filter out empty strings
        non_empty_params = filter(None, self.params)
        # Join parameters with the correct prefix
        formatted_params = '?' + "&".join(non_empty_params)
        return self.base_url + formatted_params


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

print(url)