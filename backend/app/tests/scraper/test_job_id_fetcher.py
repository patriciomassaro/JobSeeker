import pytest
import requests_mock
from app.scraper.job_ids_fetcher import JobIdsFetcher


@pytest.fixture
def job_ids_fetcher():
    return JobIdsFetcher(max_wait_time=3)


def test_perform_request_success(job_ids_fetcher):
    url = "https://example.com"
    with requests_mock.Mocker() as m:
        m.get(url, text="response", status_code=200)
        response = job_ids_fetcher.perform_request(url)
        assert response.status_code == 200


def test_perform_request_retry(job_ids_fetcher, mocker):
    url = "https://example.com"
    mock_logger = mocker.patch.object(job_ids_fetcher, "logger")
    with requests_mock.Mocker() as m:
        m.get(
            url,
            [
                {"text": "too many requests", "status_code": 429},
                {"text": "response", "status_code": 200},
            ],
        )
        response = job_ids_fetcher.perform_request(url)
        assert response.status_code == 200
        assert mock_logger.info.call_count == 1
        m.get(url, text="response", status_code=200)
        response = job_ids_fetcher.perform_request(url)
        assert response.status_code == 200


def test_get_job_ids(job_ids_fetcher):
    url = "https://example.com"
    html = """
    <html>
        <body>
            <ul>
                <li><div class="base-card" data-entity-urn="urn:li:jobPosting:12345"></div></li>
                <li><div class="base-card" data-entity-urn="urn:li:jobPosting:67890"></div></li>
            </ul>
        </body>
    </html>
    """
    with requests_mock.Mocker() as m:
        m.get(url, text=html, status_code=200)
        job_ids = job_ids_fetcher.get_job_ids(url)
        assert job_ids == ["12345", "67890"]
