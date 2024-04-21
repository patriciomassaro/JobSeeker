from jobseeker.scraper.extractors.company_extractor import CompanyExtractor
from jobseeker.scraper.database.database_manager import DatabaseManager
from jobseeker.scraper.database.models import JobPosting,Institution
from sqlalchemy import exists

db = DatabaseManager()
company_extractor = CompanyExtractor(search_page="https://www.google.com")


session = db.get_session()
# Query to find all company_urls not in the institutions table
query = session.query(JobPosting.company_url).filter(
    ~exists().where(Institution.url == JobPosting.company_url)
)
not_in_institutions = set([url[0] for url in query.all()]) 
company_extractor.process_companies_parallel(not_in_institutions,max_workers=1)






