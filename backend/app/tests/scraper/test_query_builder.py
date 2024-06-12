import pytest
from sqlmodel import Session, select
from app.models import (
    SalaryRangeFiltersEnum,
    TimeFiltersEnum,
    RemoteModalitiesEnum,
    ExperienceLevelsEnum,
    JobPostingQueries,
)
from app.scraper.query_builder import QueryBuilder, parse_input


@pytest.mark.parametrize(
    "query_parameter, input_str, expected",
    [
        ("", "", "="),
        ("q", "python developer", "q=python%20developer"),
        ("location", "new york", "location=new%20york"),
        ("location", "New York", "location=new%20york"),
    ],
)
def test_parse_input(query_parameter, input_str, expected):
    assert parse_input(query_parameter, input_str) == expected


def test_query_builder_initialization():
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    qb = QueryBuilder(base_url)
    assert qb.base_url == base_url
    assert qb.params == []


def test_add_keyword():
    qb = QueryBuilder()
    qb.add_keyword("developer")
    assert qb.params == ["keywords=developer"]
    qb.add_keyword("")
    assert qb.params[-1] == ""


def test_add_location():
    qb = QueryBuilder()
    qb.add_location("San Francisco")
    assert qb.params == ["location=san%20francisco"]
    qb.add_location("")
    assert qb.params[-1] == ""


def test_add_company_id():
    qb = QueryBuilder()
    qb.add_company_id(123)
    assert qb.params == ["f_C=123"]
    qb.add_company_id(None)
    assert qb.params[-1] == ""


def test_add_salary_range():
    qb = QueryBuilder()
    salary_range = SalaryRangeFiltersEnum.RANGE_120K_PLUS
    qb.add_salary_range(salary_range)
    assert qb.params == ["f_SB2=5"]


def test_add_time_filter():
    qb = QueryBuilder()
    time_filter = TimeFiltersEnum.PAST_WEEK
    qb.add_time_filter(time_filter)
    assert qb.params == [time_filter.get_query_param(time_filter.value, "f_TPR=r")]


def test_add_experience_level():
    qb = QueryBuilder()
    experience_level = ExperienceLevelsEnum.EXECUTIVE
    qb.add_experience_level(experience_level)
    assert qb.params == ["f_E=6"]


def test_add_remote_modality():
    qb = QueryBuilder()
    remote_modality = RemoteModalitiesEnum.REMOTE
    qb.add_remote_modality(remote_modality)
    assert qb.params == ["f_WT=2"]


def test_build_url():
    qb = QueryBuilder()
    url = (
        qb.add_keyword("machine learning engineer")
        .add_location("Washington DC")
        .add_company_id(None)  # Optional, can be omitted
        .add_salary_range(SalaryRangeFiltersEnum.RANGE_140K_PLUS)
        .add_time_filter(TimeFiltersEnum.PAST_WEEK)
        .add_experience_level(ExperienceLevelsEnum.EXECUTIVE)
        .add_remote_modality(RemoteModalitiesEnum.REMOTE)
        .build_url()
    )

    expected_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search/?keywords=machine%20learning%20engineer&location=washington%20dc&f_SB2=6&f_TPR=r604800&f_E=6&f_WT=2"

    assert url == expected_url


def test_query_builder_write_to_db(db: Session):
    expected_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search/?keywords=machine%20learning%20engineer&location=washington%20dc&f_SB2=6&f_TPR=r604800&f_E=6&f_WT=2"

    qb = QueryBuilder()
    qb.add_keyword("machine learning engineer")
    qb.add_location("Washington DC")
    qb.add_salary_range(SalaryRangeFiltersEnum.RANGE_140K_PLUS)
    qb.add_time_filter(TimeFiltersEnum.PAST_WEEK)
    qb.add_experience_level(ExperienceLevelsEnum.EXECUTIVE)
    qb.add_remote_modality(RemoteModalitiesEnum.REMOTE)
    url = qb.build_url_and_write_to_db()

    query = db.exec(
        select(JobPostingQueries).where(JobPostingQueries.url == url)
    ).first()

    assert query
    assert query.url == expected_url
    assert query.keywords == "machine learning engineer"
    assert query.location == "Washington DC"
    assert query.salary_range_id == 6
    assert query.time_filter_id == 2
    assert query.experience_level_id == 6
    assert query.remote_modality_id == 2

    db.delete(query)
    db.commit()
