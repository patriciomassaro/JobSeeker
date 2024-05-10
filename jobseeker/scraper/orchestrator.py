import requests
import time
import random
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import itertools

from jobseeker.scraper.extractors.job_postings_extractor import JobPostingDataExtractor
from jobseeker.scraper.query_builder.query_builder import QueryBuilder
from jobseeker.scraper.query_builder.query_builder import FilterRemoteModality, FilterSalaryRange, FilterTime,FilterExperienceLevel
from jobseeker.logger import Logger
from jobseeker.database import DatabaseManager
from jobseeker.database.models import JobQueryResult,JobQuery,JobPosting


class MainOrchestrator:
    """
    Main orchestrator class that will handle obtaining the job postings, writing them to the database, and adding the job query results to the database.
    """

    def __init__(self,
                 job_posting_max_workers=1,
                 company_max_workers=1,
                 jobs_base_url="https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search",
                 log_file_name="scraper.log"):
        self.logger = Logger(prefix="Orchestrator",log_file_name=log_file_name).get_logger()
        self.job_extractor= JobPostingDataExtractor()
        self.query_builder= QueryBuilder(base_url=jobs_base_url)
        self.database_manager= DatabaseManager()
        self.job_extractor= JobPostingDataExtractor()
        self.job_posting_max_workers = job_posting_max_workers
        self.company_max_workers = company_max_workers

    def perform_request(self,url):
        maximum_retries= 30
        retry_count =0
        while retry_count < maximum_retries:
            job_request = requests.get(url)
            if job_request.status_code == 200:
                return job_request
            if job_request.status_code == 429:
                self.logger.info("Too many requests, waiting before retrying...")
                time.sleep(random.randint(1,30))
                retry_count += 1
                continue
        self.logger.error(f"Failed to extract data for url: {url}")
        return None

    def get_job_ids(self,url):
        request = self.perform_request(url)
        if request is None:
            return []
        list_data = request.text
        list_soup = BeautifulSoup(list_data, 'html.parser')
        page_jobs = list_soup.find_all('li')
        job_id_list = [job.find('div', class_='base-card')['data-entity-urn'].split(":")[-1] for job in page_jobs if job.find('div', class_='base-card')]
        self.logger.info(f"Extracted {len(job_id_list)} job ids")
        
        return job_id_list

    def get_job_ids_with_check(self, url, start):
        # This method fetches job IDs and checks their count
        partial_url = url + f"&start={start}"
        job_ids = self.get_job_ids(partial_url)
        return job_ids,len(job_ids) <= 8

    def fetch_job_ids_in_parallel(self, base_url, num_batches,batch_start):
        # This method is responsible for fetching job IDs in parallel
        with ThreadPoolExecutor(max_workers=self.job_posting_max_workers) as executor:
            # Prepare futures for parallel execution
            futures = [executor.submit(self.get_job_ids_with_check, base_url, batch_num * 10) for batch_num in range(batch_start, batch_start + num_batches)]
            job_results = []
            flag_results = []
            
            for future in as_completed(futures):
                job_ids, is_last_batch = future.result()
                job_results.append(job_ids)
                flag_results.append(is_last_batch)
            return job_results, any(flag_results)

    def add_job_query_results_to_database(self,job_ids:list[int], query_id:int):
        self.logger.info(f"Adding relation between job query {query_id} and job postings")
        session = self.database_manager.get_session()
        for job_id in job_ids:
            job_posting_primary_key = session.query(JobPosting.id).filter(JobPosting.id == job_id).scalar()
            job_query_result = JobQueryResult(job_query_id=query_id, job_posting_id=job_posting_primary_key)
            session.close()
            self.database_manager.add_object(job_query_result)
        


    def run_scraping_job(self,
        keywords:str=None,
        location:str=None,
        salary_range:FilterSalaryRange=None,
        time_filter:FilterTime=None,
        experience_level:FilterExperienceLevel=None,
        remote_modality:FilterRemoteModality=None,
        company_id:str= None
    ):
        if keywords:
            self.query_builder.add_keyword(keywords)
        if location:
            self.query_builder.add_location(location)
        if salary_range:
            self.query_builder.add_salary_range(salary_range)
        if time_filter:
            self.query_builder.add_time_filter(time_filter)
        if experience_level:
            self.query_builder.add_experience_level(experience_level)
        if remote_modality:
            self.query_builder.add_remote_modality(remote_modality)
        if company_id:
            self.query_builder.add_company_id(company_id)

        url,query_id = self.query_builder.build_url()
        batch_start=0
        job_ids = []
        # We fetch all the possible job_ids
        while True:
            fetched_ids,process_should_stop_flag = self.fetch_job_ids_in_parallel(url, num_batches=self.job_posting_max_workers, batch_start=batch_start)
            job_ids.extend(list(itertools.chain(*fetched_ids)))
            if process_should_stop_flag:
                break
            batch_start += 10   
        # Remove duplicates
        job_ids = list(set(job_ids)) 
        # Now that we have all the job_ids, we can start scraping the job postings
        scraped_job_postings=self.job_extractor.extract_job_postings(job_ids=job_ids,max_workers=self.job_posting_max_workers)
        self.add_job_query_results_to_database(job_ids,query_id)
        self.logger.info("Finished scraping job postings")
if __name__ == "__main__":


    # define the query builder
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    orchestrator = MainOrchestrator(jobs_base_url=base_url,
                                    job_posting_max_workers=10,
                                    company_max_workers=2)

    orchestrator.run_scraping_job(
        keywords="machine learning",
        location="United States",
        salary_range=FilterSalaryRange.RANGE_ANY,
        time_filter=FilterTime.ANY_TIME,
        experience_level=FilterExperienceLevel.ANY_EXPERIENCE_LEVEL,    
        remote_modality=FilterRemoteModality.ANY_MODALITY,
        company_id=3991657
    )

    