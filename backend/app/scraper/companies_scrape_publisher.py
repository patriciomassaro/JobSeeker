from sqlmodel import Session, select, exists
from app.models import JobPostings, Institutions
from app.core.db import engine
from app.scraper.rabbit_mq_handler import RabbitMQHandler


with Session(engine) as session:
    # Building the query
    statement = select(JobPostings.company_url).where(
        ~exists().where(Institutions.url == JobPostings.company_url)
    )
    # Executing the query
    companies_to_scrape = session.execute(statement)
    not_in_institutions = set(url[0] for url in companies_to_scrape.all())

rabbitmq_handler = RabbitMQHandler(log_file_name="consumer.log")

# Declaring the queue
rabbitmq_handler.declare_queue("companies_to_scrape")

# Publishing the messages
for url in not_in_institutions:
    rabbitmq_handler.publish_message(url, "companies_to_scrape")
    print(f"Published {url} to companies_to_scrape")
