import pytest
from bs4 import BeautifulSoup
from jobseeker.scraper.job_postings_extractor import JobPostingDataExtractor

@pytest.fixture
def job_soup():
    # Create a sample BeautifulSoup object for testing
    html = """
    <html>
        <body>
            <div class="show-more-less-html__markup">
                <strong>Heading 1</strong>
                <p>Paragraph 1</p>
                <strong>Heading 2</strong>
                <p>Paragraph 2</p>
                <ul>
                    <li>List item 1</li>
                    <li>List item 2</li>
                </ul>
            </div>
        </body>
    </html>
    """
    return BeautifulSoup(html, 'html.parser')

def test_extract_job_description(job_soup):
    extractor = JobPostingDataExtractor()
    expected_result = "Heading 1\n\nParagraph 1\n\nHeading 2\n\nParagraph 2\n\n- List item 1\n- List item 2"
    assert extractor.extract_job_description(job_soup) == expected_result

def test_extract_job_criteria(job_soup):
    extractor = JobPostingDataExtractor()
    expected_result = {
        "Criteria 1": "Detail 1",
        "Criteria 2": "Detail 2"
    }
    assert extractor.extract_job_criteria(job_soup) == expected_result

def test_extract_job_poster(job_soup):
    extractor = JobPostingDataExtractor()
    expected_result = {
        "name": "John Doe",
        "title": "Recruiter",
        "profile_url": "https://www.linkedin.com/in/johndoe"
    }
    assert extractor.extract_job_poster(job_soup) == expected_result

def test_extract_salaries():
    extractor = JobPostingDataExtractor()
    job_description = "The salary range is $50,000 - $70,000 USD per year"
    expected_result = ["$50,000 - $70,000 USD"]
    assert extractor.extract_salaries(job_description) == expected_result

def test_extract_data(job_soup):
    extractor = JobPostingDataExtractor()
    job_id = "12345"
    expected_result = JobPosting(
        job_id="12345",
        title="Job Title",
        seniority_level="Senior",
        employment_type="Full-time",
        job_description="Job description",
        company="Company Name",
        company_url="https://www.company.com",
        job_functions="Function 1, Function 2",
        industries="Industry 1, Industry 2",
        job_poster_profile_url="https://www.linkedin.com/in/johndoe",
        job_poster_name="John Doe"
    )
    assert extractor.extract_data(job_id) == expected_result