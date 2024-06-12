from typing import ChainMap
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup
from sqlmodel import Session, select

from app.models import Institutions
from app.scraper.extractors.company_extractor import CompanyExtractor

HTML_COMPANY_1 = """
<div class="mb-2" data-test-id="about-us__size">
    <dd>51-200 employees</dd>
</div>
<h3 class="top-card-layout__first-subline font-sans text-md leading-open text-color-text-low-emphasis">
    San Francisco, CA 10,000 followers
</h3>
<p class="break-words whitespace-pre-wrap text-color-text">Test about section 1</p>
<h1 class="top-card-layout__title">Test Company 1</h1>
<h2 class="top-card-layout__headline">Software Development</h2>
<a class="link-no-visited-state hover:no-underline">www.testcompany1.com</a>
<div class="mb-2" data-test-id="about-us__specialties">
    <dd>Specialty 1, Specialty 2</dd>
</div>
<a class="face-pile__cta">View all 1,001 employees</a>
<h4 class="top-card-layout__second-subline">
    We're building an open financial system for the world.
</h4>
"""

HTML_COMPANY_2 = """
<div class="mb-2" data-test-id="about-us__size">
    <dd>201-500 employees</dd>
</div>
<h3 class="top-card-layout__first-subline font-sans text-md leading-open text-color-text-low-emphasis">
    New York, NY 20,000 followers
</h3>
<p class="break-words whitespace-pre-wrap text-color-text">Test about section 2</p>
<h1 class="top-card-layout__title">Test Company 2</h1>
<h2 class="top-card-layout__headline">Financial Services</h2>
<a class="link-no-visited-state hover:no-underline">www.testcompany2.com</a>
<div class="mb-2" data-test-id="about-us__specialties">
    <dd>Specialty A, Specialty B</dd>
</div>
<a class="face-pile__cta">View all 2,000,001 employees</a>
<h4 class="top-card-layout__second-subline">
    We provide innovative financial solutions.
</h4>
"""

HTML_WITHOUT_DATA = """
<div class="no-data">
    No data available
</div>
"""


@pytest.fixture
def html_with_data():
    return BeautifulSoup(HTML_COMPANY_1, "html.parser")


@pytest.fixture
def html_without_data():
    return BeautifulSoup(HTML_COMPANY_1, "html.parser")


@pytest.fixture
def driver_mock():
    driver = MagicMock()
    driver.get.return_value = None
    driver.page_source = HTML_COMPANY_1
    return driver


@pytest.fixture
def session_mock(mocker):
    return mocker.patch(
        "app.scraper.extractors.company_extractor.Session", autospec=True
    )


def test_get_location():
    extractor = CompanyExtractor()
    assert (
        extractor.get_location("San Francisco, CA 10,000 followers")
        == "San Francisco, CA"
    )


def test_get_followers():
    extractor = CompanyExtractor()
    assert extractor.get_followers("San Francisco, CA 10,000 followers") == 10000


def test_get_about(html_with_data):
    extractor = CompanyExtractor()
    assert extractor.get_about(html_with_data) == "Test about section 1"


def test_get_employees(html_with_data):
    extractor = CompanyExtractor()
    assert extractor.get_employees(html_with_data) == 1001


def test_get_tagline(html_with_data):
    extractor = CompanyExtractor()
    assert (
        extractor.get_tagline(html_with_data)
        == "We're building an open financial system for the world."
    )


def test_get_company_name(html_with_data):
    extractor = CompanyExtractor()
    assert extractor.get_company_name(html_with_data) == "Test Company 1"


def test_get_industry(html_with_data):
    extractor = CompanyExtractor()
    assert extractor.get_industry(html_with_data) == "Software Development"


def test_get_website(html_with_data):
    extractor = CompanyExtractor()
    assert extractor.get_website(html_with_data) == "www.testcompany1.com"


def test_get_size(html_with_data):
    extractor = CompanyExtractor()
    with patch(
        "app.scraper.extractors.company_extractor.InstitutionSizesEnum.get_id",
        return_value=3,
    ):
        assert extractor.get_size(html_with_data) == 3


def test_get_specialties(html_with_data):
    extractor = CompanyExtractor()
    assert extractor.get_specialties(html_with_data) == ["Specialty 1", "Specialty 2"]


def test_parse_company_html():
    extractor = CompanyExtractor()
    result = extractor.parse_company_html(HTML_COMPANY_1)
    assert result["name"] == "Test Company 1"
    assert result["location"] == "San Francisco, CA"
    assert result["about"] == "Test about section 1"
    assert result["website"] == "www.testcompany1.com"
    assert result["industry"] == "Software Development"
    assert result["size"] == 2
    assert result["specialties"] == ["Specialty 1", "Specialty 2"]
    assert result["followers"] == 10000
    assert result["employees"] == 1001
    assert result["tagline"] == "We're building an open financial system for the world."


@patch("selenium.webdriver.Chrome")
@patch("app.scraper.extractors.company_extractor.ChromeDriverManager.install")
def test_process_company(mock_chrome_driver_manager, mock_chrome, session_mock):
    # Set up mocks
    mock_chrome.return_value = driver_mock
    mock_chrome_driver_manager.return_value = "/path/to/chromedriver"

    extractor = CompanyExtractor()
    with patch.object(
        extractor, "search_linkedin_company_and_get_html", return_value=HTML_COMPANY_1
    ):
        result = extractor.process_company("www.linkedin.com/company/test-company")

    assert result.url == "www.linkedin.com/company/test-company"
    assert result.name == "Test Company 1"
    assert result.location == "San Francisco, CA"
    assert result.about == "Test about section 1"
    assert result.website == "www.testcompany1.com"
    assert result.industry == "Software Development"
    assert result.size == 2
    assert result.specialties == ["Specialty 1", "Specialty 2"]
    assert result.followers == 10000
    assert result.employees == 1001
    assert result.tagline == "We're building an open financial system for the world."

    # Verify that the company was written to the database
    session_mock.return_value.__enter__.return_value.merge.assert_called_once()
    session_mock.return_value.__enter__.return_value.commit.assert_called_once()


def test_merge_get_delete_company(db: Session):
    extractor = CompanyExtractor()

    # Mocked company data
    company_data = {
        "url": "www.linkedin.com/company/test-company",
        "name": "Test Company",
        "location": "San Francisco, CA",
        "about": "Test about section",
        "website": "www.testcompany.com",
        "industry": "Software Development",
        "size": 3,
        "specialties": ["Specialty 1", "Specialty 2"],
        "followers": 10000,
        "employees": 1001,
        "tagline": "We're building an open financial system for the world.",
    }
    institution = Institutions(**company_data)

    extractor.write_company_to_database(institution)

    # Retrieve the recently inserted company using session.exec()
    statement = select(Institutions).where(Institutions.url == company_data["url"])
    inserted_company = db.exec(statement).first()

    assert inserted_company is not None
    assert inserted_company.name == company_data["name"]
    assert inserted_company.location == company_data["location"]
    assert inserted_company.about == company_data["about"]
    assert inserted_company.website == company_data["website"]
    assert inserted_company.industry == company_data["industry"]
    assert inserted_company.size == company_data["size"]
    assert inserted_company.specialties == company_data["specialties"]
    assert inserted_company.followers == company_data["followers"]
    assert inserted_company.employees == company_data["employees"]
    assert inserted_company.tagline == company_data["tagline"]

    # Delete the inserted company
    db.delete(inserted_company)
    db.commit()

    # Verify the company has been deleted using session.exec()
    deleted_company = db.get(Institutions, inserted_company.id)
    assert deleted_company is None


def test_process_companies_parallel(db: Session):
    # Mocked company data
    company_data_1 = {
        "url": "www.linkedin.com/company/test-company1",
        "name": "Test Company 1",
        "location": "San Francisco, CA",
        "about": "Test about section 1",
        "website": "www.testcompany1.com",
        "industry": "Software Development",
        "size": 2,
        "specialties": ["Specialty 1", "Specialty 2"],
        "followers": 10000,
        "employees": 1001,
        "tagline": "We're building an open financial system for the world.",
    }

    company_data_2 = {
        "url": "www.linkedin.com/company/test-company2",
        "name": "Test Company 2",
        "location": "New York, NY",
        "about": "Test about section 2",
        "website": "www.testcompany2.com",
        "industry": "Financial Services",
        "size": 3,
        "specialties": ["Specialty A", "Specialty B"],
        "followers": 20000,
        "employees": 2000001,
        "tagline": "We provide innovative financial solutions.",
    }

    # Mock the search_linkedin_company_and_get_html method to return our HTML_COMPANY_1 and HTML_COMPANY_2
    def mock_search_linkedin_company_and_get_html(self, company_url, driver, wait):
        print(f"Mock called for URL: {company_url}")
        if "test-company1" in company_url:
            return HTML_COMPANY_1
        elif "test-company2" in company_url:
            return HTML_COMPANY_2
        else:
            return None

    with patch.object(
        CompanyExtractor,
        "search_linkedin_company_and_get_html",
        mock_search_linkedin_company_and_get_html,
    ):
        extractor = CompanyExtractor()

        companies = [
            "www.linkedin.com/company/test-company1",
            "www.linkedin.com/company/test-company2",
            "www.linkedin.com/company/test-company1",
            "www.linkedin.com/company/test-company2",
            "www.linkedin.com/company/test-company1",
            "www.linkedin.com/company/test-company2",
            "www.linkedin.com/company/test-company1",
        ]
        results = extractor.process_companies_parallel(companies, max_workers=10)

    assert len(results) == len(companies)

    # Verify the companies are inserted into the database
    statement_1 = select(Institutions).where(Institutions.url == company_data_1["url"])
    statement_2 = select(Institutions).where(Institutions.url == company_data_2["url"])

    company_1 = db.exec(statement_1).first()
    company_2 = db.exec(statement_2).first()

    companies_1 = db.exec(statement_1).all()
    companies_2 = db.exec(statement_2).all()

    assert company_1 is not None
    assert company_1.name == company_data_1["name"]
    assert company_1.location == company_data_1["location"]
    assert company_1.about == company_data_1["about"]
    assert company_1.website == company_data_1["website"]
    assert company_1.industry == company_data_1["industry"]
    assert company_1.size == company_data_1["size"]
    assert company_1.specialties == company_data_1["specialties"]
    assert company_1.followers == company_data_1["followers"]
    assert company_1.employees == company_data_1["employees"]
    assert company_1.tagline == company_data_1["tagline"]

    assert company_2 is not None
    assert company_2.name == company_data_2["name"]
    assert company_2.location == company_data_2["location"]
    assert company_2.about == company_data_2["about"]
    assert company_2.website == company_data_2["website"]
    assert company_2.industry == company_data_2["industry"]
    assert company_2.size == company_data_2["size"]
    assert company_2.specialties == company_data_2["specialties"]
    assert company_2.followers == company_data_2["followers"]
    assert company_2.employees == company_data_2["employees"]
    assert company_2.tagline == company_data_2["tagline"]

    for company in companies_1:
        db.delete(company)
    for company in companies_2:
        db.delete(company)

    db.commit()
