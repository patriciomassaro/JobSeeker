import pytest
import requests_mock
from app.scraper.job_ids_fetcher import JobIdsFetcher
import pika


test_base_url = "https://example.com?param=value"
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


html_single_job = """
    <html>
        <body>
            <ul>
                <li><div class="base-card" data-entity-urn="urn:li:jobPosting:12345"></div></li>
            </ul>
        </body>
    </html>
"""


@pytest.fixture(scope="module")
def rabbitmq_connection():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host="rabbitmq",  # Use 'localhost' if running RabbitMQ locally, or the service name if in Docker Compose
            port=5672,
            credentials=pika.PlainCredentials("user", "password"),
        )
    )
    yield connection
    connection.close()


@pytest.fixture
def job_ids_fetcher(rabbitmq_connection):
    return JobIdsFetcher(job_ids_fetch_workers=1, jobs_base_url=test_base_url)


def test_get_job_ids_with_check(job_ids_fetcher):
    with requests_mock.Mocker() as m:
        m.get(test_base_url + "&start=0", text=html, status_code=200)
        job_ids, process_should_stop_flag = job_ids_fetcher.get_job_ids_with_check(
            test_base_url, 0
        )
        assert "12345" in job_ids
        assert "67890" in job_ids
        assert process_should_stop_flag


def test_fetch_job_ids_integration(job_ids_fetcher, rabbitmq_connection):
    with requests_mock.Mocker() as m:
        paginated_url = f"{test_base_url}&start=0"
        m.get(paginated_url, text=html, status_code=200)

        job_ids, process_should_stop_flag = job_ids_fetcher.fetch_job_ids_in_parallel(
            test_base_url, 0
        )
        assert len(job_ids) == 1
        assert "12345" in job_ids[0]
        assert "67890" in job_ids[0]
        assert process_should_stop_flag

        paginated_url = f"{test_base_url}&start=1"
        m.get(paginated_url, text=html_single_job, status_code=200)

        job_ids_fetcher_with_one_job_id_per_request = JobIdsFetcher(
            job_ids_fetch_workers=1, jobs_base_url=test_base_url, ids_per_request=1
        )
        job_ids, process_should_stop_flag = (
            job_ids_fetcher_with_one_job_id_per_request.fetch_job_ids_in_parallel(
                test_base_url, 1
            )
        )
        assert len(job_ids) == 1
        assert "12345" in job_ids[0]
        assert "67890" not in job_ids[0]
        assert not process_should_stop_flag


def test_run_scraping_job_integration(job_ids_fetcher, rabbitmq_connection):
    with requests_mock.Mocker() as m:
        paginated_url = f"{test_base_url}?keywords=test&location=test&start={0}"
        m.get(paginated_url, text=html, status_code=200)

        # Declare the queue before running the job
        channel = rabbitmq_connection.channel()
        channel.queue_declare(queue=job_ids_fetcher.rabbitmq_queue_name)

        job_ids_fetcher.run_scraping_job(keywords="test", location="test")

        # Verify messages in RabbitMQ
        method_frame, header_frame, body = channel.basic_get(
            job_ids_fetcher.rabbitmq_queue_name
        )

        assert (
            method_frame is not None
        ), "Expected a message in the queue, but found none."
        assert body.decode() in ["12345", "67890"]
        channel.basic_ack(method_frame.delivery_tag)
