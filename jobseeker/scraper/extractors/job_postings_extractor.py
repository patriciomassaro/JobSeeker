import requests
from bs4 import BeautifulSoup
import random
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from jobseeker.scraper.datatypes  import JobPosting  as JobPosting
from jobseeker.scraper.database.models import JobPosting as JobPostingDBModel
from jobseeker.scraper.logger import ExtractorLogger

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Update these values according to your database configuration
DATABASE_URL = "postgresql+psycopg2://postgres:holaguada2@localhost/jobseeker"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)



JOB_POSTING_BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"
MAXIMUM_RETRY_WAIT_TIME = 10
MAXIMUM_RETRIES = 10
WAIT_TIME_BETWEEN_REQUESTS_LIMITS = (1, 5)

class JobPostingDataExtractor:
    def __init__(self,
                 log_file_name: str = "scraper.log",
                 job_posting_base_url: str = JOB_POSTING_BASE_URL,
                 maximum_retries: int = MAXIMUM_RETRIES,
                 retry_wait_time: int = MAXIMUM_RETRY_WAIT_TIME,
                 wait_time_limits: tuple = WAIT_TIME_BETWEEN_REQUESTS_LIMITS):
        self.logger = ExtractorLogger(prefix="JobPostingDataExtractor",log_file_name=log_file_name).get_logger()
        self.job_posting_base_url = JOB_POSTING_BASE_URL
        self.maximum_retries = maximum_retries
        self.retry_wait_time = retry_wait_time
        self.wait_time_limits = wait_time_limits

    @staticmethod
    def extract_job_description(job_soup: BeautifulSoup) -> str:
        """
        Extracts and formats the job description from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Formatted job description text
        """
        formatted_text_pieces = []
        job_description_tag=job_soup.find("div", {"class": "show-more-less-html__markup"})
        # Extract and format <strong> elements and following siblings until the next <strong> element or list
        for child in job_description_tag.children:
            if child.name == "strong":
                    # Format headings
                    formatted_text_pieces.append(f"{child.get_text().strip()}\n")
            elif child.name == "p":
                # Format paragraphs, handling <br> tags as new lines
                text = child.get_text(separator="\n", strip=True)
                formatted_text_pieces.append(text)
            elif child.name in ["ul", "ol"]:
                # Format lists
                list_items = [li.get_text(separator="\n", strip=True) for li in child.find_all("li")]
                formatted_list = "\n".join([f"- {item}" for item in list_items])
                formatted_text_pieces.append(formatted_list)
            elif child.name == "br":
                # Optionally, handle breaks if needed
                continue
            else:
                # Handle other types of elements as needed or ignore
                text = child.get_text(separator="\n", strip=True)
                if text:
                    formatted_text_pieces.append(text)

        # Join the formatted text pieces into a single string
        formatted_text = "\n\n".join(formatted_text_pieces)

        return formatted_text

    @staticmethod
    def extract_job_criteria(job_soup: BeautifulSoup) -> dict:
        """
        Extracts and formats the job criteria from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Dictionary of job criteria
        """
        criteria_dict = {}
        job_criteria = job_soup.find_all("li", class_="description__job-criteria-item")
        # Extracting and printing each component
        for item in job_criteria:
            # Extract the criteria name and detail
            criteria_name = item.find("h3", class_="description__job-criteria-subheader").text.strip()
            criteria_detail = item.find("span", class_="description__job-criteria-text description__job-criteria-text--criteria").text.strip()

            # Add to the dictionary
            criteria_dict[criteria_name] = criteria_detail

        return criteria_dict
        
    @staticmethod
    def extract_job_poster(job_soup: BeautifulSoup) -> dict:
        name = ""
        profile_url = ""
        message_recruiter_div = job_soup.find("div", class_="message-the-recruiter")
        if message_recruiter_div:
            # If the div exists, find the <a> tag for the URL and name
            profile_tag = message_recruiter_div.find("a", class_="base-card__full-link absolute top-0 right-0 bottom-0 left-0 p-0 z-[2]")
            # Find the <h4> tag within the div for the detailed title
            detail_title_tag = message_recruiter_div.find("h4", class_="base-main-card__subtitle body-text text-color-text overflow-hidden")
            
            if profile_tag and detail_title_tag:
                # Extract the name, which is also visually hidden but available for screen readers
                name = profile_tag.find("span", class_="sr-only").text.strip() if profile_tag.find("span", class_="sr-only") else None
                # Extract the profile URL
                profile_url = profile_tag.get('href', None).split("?trk")[0] if profile_tag.get('href', None) else None

                # Extract the title
                title = detail_title_tag.text.strip()
                # Compile the extracted information
                info = {
                    "name": name,
                    "title": title,
                    "profile_url": profile_url
                }
                return info
        else:
            return None

    @staticmethod
    def extract_salaries(job_description: str) -> list:
        # This pattern focuses on:
        # - Optional dollar sign
        # - Numbers potentially starting with $, possibly with a comma or period for thousands, and may end with "K" for thousands or specify "USD"
        # - Ignores solitary small numbers that are unlikely to represent salaries

        pattern = r'\$\d{1,3}(?:[.,]\d{3})*(?:-\$\d{1,3}(?:[.,]\d{3})*)?\s?(?:k|K|USD|usd)?|\d{1,3}(?:[.,]\d{3})+(?:-\d{1,3}(?:[.,]\d{3})*)?\s?(?:k|K|USD|usd)'

        
        # Find all matches in the job description
        matches = re.findall(pattern, job_description)
        
        # Process matches to standardize format (optional, depending on your needs)
        standardized_matches = [match.replace(',', '').replace('.', '').upper() for match in matches]
        
        return standardized_matches

    def extract_single_job_posting(self,job_id: str) -> JobPosting:
        job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        self.logger.info(f"{job_id} - Scraping job")
        retries= 0
        while retries < self.maximum_retries :
            wait_time = random.randint(*self.wait_time_limits)
            self.logger.info(f"{job_id} - Waiting {wait_time} seconds")
            time.sleep(wait_time)
            job_request = requests.get(job_url)
            if job_request.status_code == 429:
                self.logger.info(f"{job_id} - Too many requests, waiting {self.retry_wait_time} secs...")
                time.sleep(self.retry_wait_time)
                retries += 1
                continue
            job_data = job_request.text
            job_soup = BeautifulSoup(job_data, 'html.parser')

            ###### Data Extraction
            job_title = job_soup.find("h2", {"class": "top-card-layout__title font-sans text-lg papabear:text-xl font-bold leading-open text-color-text mb-0 topcard__title"}).text.strip()
            company_name = job_soup.find("a", {"class": "topcard__org-name-link topcard__flavor--black-link"}).text.strip()
            company_url = job_soup.find("a", {"class": "topcard__org-name-link topcard__flavor--black-link"})['href'].split("?trk")[0]
            job_location = job_soup.find("span", {"class": "topcard__flavor topcard__flavor--bullet"}).text.strip()


            # Extract data using the other methods
            job_description_text = self.extract_job_description(job_soup)
            job_criteria_dict = self.extract_job_criteria(job_soup)
            job_poster_info = self.extract_job_poster(job_soup)
            salary = self.extract_salaries(job_description_text)

            # You might need to adjust this part based on how you're initializing JobPosting
            job_posting = JobPosting(
                job_id=job_id,
                title=job_title,
                seniority_level=job_criteria_dict.get("Seniority level", None),
                employment_type=job_criteria_dict.get("Employment type", None),
                job_description=job_description_text,
                company=company_name,
                company_url=company_url,
                job_functions=job_criteria_dict.get("Job function", None),
                industries=job_criteria_dict.get("Industries", None),
            )
            if job_poster_info:
                job_posting.job_poster_profile_url = job_poster_info.get("profile_url", None)
                job_posting.job_poster_name = job_poster_info.get("name", None)

            
            return job_posting
        self.logger.error(f"{job_id} Failed to extract data after {self.maximum_retries} retries.")
        return None
    
    def extract_job_postings(self, job_ids: list[str], max_workers: int = 5) -> list:
        """
        Extracts data for multiple job postings in parallel.
        
        :param job_ids: A list of job ID strings.
        :param max_workers: Maximum number of threads to use.
        :return: A list of JobPosting objects (or None for failed extractions).
        """
        job_postings = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Map each job ID to a future object
            future_to_job_id = {executor.submit(self.extract_single_job_posting, job_id): job_id for job_id in job_ids}
            
            for future in as_completed(future_to_job_id):
                job_id = future_to_job_id[future]
                try:
                    job_posting = future.result()
                    job_postings.append(job_posting)
                except Exception as exc:
                    print(f'Job ID {job_id} generated an exception: {exc}')
                    job_postings.append(None)
        
        return job_postings

    def write_job_postings_to_database(self, session, job_postings: list):
        for job_posting in job_postings:
            try:
                if job_posting:
                    session.add(JobPostingDBModel(**job_posting.to_dict()))
                    session.commit()
                    self.logger.info(f"Job posting {job_posting.job_id} added to the database")
            except Exception as e:
                session.rollback()
                self.logger.error(f"Failed to add job posting {job_posting.job_id} to the database: {e}")
            finally:
                session.close()


if __name__ == "__main__":
    job_ids = [3842512500,3885598758,3820465141,3847787255,3871524017]
    start = time.time()
    extractor = JobPostingDataExtractor()
    job_postings = extractor.extract_job_postings(job_ids, max_workers=5)
    end = time.time()
    print(f"Time taken: {end - start} seconds, got {len(job_postings)} job postings")

    extractor.write_job_postings_to_database(Session(), job_postings)

