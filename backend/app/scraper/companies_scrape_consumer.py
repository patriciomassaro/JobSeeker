from app.scraper.extractors.company_extractor import CompanyExtractor
from app.logger import Logger
from sqlmodel import Session, select, exists
from app.models import JobPostings, Institutions
from app.core.db import engine
import random

logger = Logger(
    prefix="CompaniesScraper", log_file_name="companies_scraper.log"
).get_logger()


def get_companies_to_scrape():
    with Session(engine) as session:
        # Building the query
        statement = select(JobPostings.company_url).where(
            ~exists().where(Institutions.url == JobPostings.company_url)  # type: ignore
        )
        # Executing the query
        companies_to_scrape = session.exec(statement).all()
        not_in_institutions = set(companies_to_scrape)
        return list(not_in_institutions)


def scrape_companies(companies: list[str | None], max_workers: int, batch_size: int):
    companies_to_scrape = random.sample(companies, batch_size)
    print(companies_to_scrape)
    extractor = CompanyExtractor(log_file_name="companies_scraper.log", wait_time=300)
    extractor.process_companies_parallel(
        company_urls=companies_to_scrape,  # type: ignore
        max_workers=max_workers,
    )


if __name__ == "__main__":
    companies = get_companies_to_scrape()
    print(companies)
    if companies:
        scrape_companies(companies, max_workers=10, batch_size=10)
