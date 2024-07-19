from sqlmodel import Session, select, exists
from app.models import JobPostings, Institutions
from app.core.db import engine
from app.scraper.rabbit_mq_handler import RabbitMQHandler


with Session(engine) as session:
    # Building the query
    statement = select(JobPostings.company_url).where(
        ~exists().where(Institutions.url == JobPostings.company_url)  # type: ignore
    )
    # Executing the query
    companies_to_scrape = session.exec(statement).all()
    not_in_institutions = set(companies_to_scrape)

rabbitmq_handler = RabbitMQHandler(log_file_name="consumer.log")

# Declaring the queue
rabbitmq_handler.declare_queue("companies_to_scrape")

# Publishing the messages
for url in not_in_institutions:
    rabbitmq_handler.publish_message(url, "companies_to_scrape")
