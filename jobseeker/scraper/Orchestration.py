import requests
import time
import random
from bs4 import BeautifulSoup

from jobseeker.scraper.job_postings_extractor import JobPostingDataExtractor
from jobseeker.scraper.query_builder import QueryBuilder
from jobseeker.scraper.query_builder import FilterRemoteModality, FilterSalaryRange, FilterTime,FilterExperienceLevel

from jobseeker.scraper.datatypes import JobPosting


def perform_request(url):
    maximum_retries= 10
    retry_count =0
    while retry_count < maximum_retries:
        wait_time = random.randint(1, 5)
        # print(f"Waiting {wait_time} seconds")
        time.sleep(wait_time)
        job_request = requests.get(url)
        if job_request.status_code == 200:
            return job_request
        if job_request.status_code == 429:
            # print("Too many requests, waiting 10 seconds before retrying...")
            time.sleep(10)
            retry_count += 1
            continue
    # print(f"Failed to extract data for job ID: {job_id}")
    return None

def get_job_ids(url):
    request = perform_request(url)
    if request is None:
        return []
    list_data = request.text
    list_soup = BeautifulSoup(list_data, 'html.parser')
    page_jobs = list_soup.find_all('li')
    job_id_list = [job.find('div', class_='base-card')['data-entity-urn'].split(":")[-1] for job in page_jobs if job.find('div', class_='base-card')]
    return job_id_list

if __name__ == "__main__":

    # define the query builder
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    query_builder = QueryBuilder(base_url)

    job_extractor=JobPostingDataExtractor(job_posting_base_url="https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/",
                                          maximum_retries=10,
                                          wait_time_limits=(1, 5),
                                          retry_wait_time=3)

    start = 0
    job_list = []
    while True:
        url = (query_builder.add_keyword("machine learning engineer")
            .add_location("United States")
            .add_company_id(None)  # Optional, can be omitted
            .add_salary_range(FilterSalaryRange.RANGE_140K_PLUS)
            .add_time_filter(FilterTime.PAST_WEEK)
            .add_experience_level(FilterExperienceLevel.ANY_EXPERIENCE_LEVEL)
            .add_remote_modality(FilterRemoteModality.REMOTE)
            .build_url() + f"&start={start}")

        job_ids = get_job_ids(url)
        

        for job_id in job_ids:
            job_list.append(job_id)
            job_post = job_extractor.extract_data(job_id=job_id)

            print("//ID: ",job_post.job_id,"//Company: ",job_post.company,"// Title: ",job_post.title)
        
        if len(job_ids) < 10:  # Less than 10 jobs indicates end of list
            break

        start += 10  # Prepare the 'start' parameter for the next batch of jobs
    print(job_list)
        

    