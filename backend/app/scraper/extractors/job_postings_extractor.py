import requests
from bs4 import BeautifulSoup
import random
import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from jobseeker.scraper.datatypes  import JobPosting  as JobPosting
from jobseeker.database.models import JobPosting as JobPostingDBModel
from jobseeker.logger import Logger
from jobseeker.database import DatabaseManager 





JOB_POSTING_BASE_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/"
MAXIMUM_RETRIES = 40
WAIT_TIME_BETWEEN_REQUESTS_LIMITS = (1, 30)

class JobPostingDataExtractor:
    def __init__(self,
                 log_file_name: str = "scraper.log",
                 job_posting_base_url: str = JOB_POSTING_BASE_URL,
                 maximum_retries: int = MAXIMUM_RETRIES,
                 wait_time_limits: tuple = WAIT_TIME_BETWEEN_REQUESTS_LIMITS):
        self.logger = Logger(prefix="JobPostingDataExtractor",log_file_name=log_file_name).get_logger()
        self.job_posting_base_url = JOB_POSTING_BASE_URL
        self.maximum_retries = maximum_retries
        self.wait_time_limits = wait_time_limits

    @staticmethod
    def _extract_job_criteria_based_on_string(job_soup: BeautifulSoup, text:str) -> str:
        # Iterate through each li element
        for li in job_soup.select('.description__job-criteria-item'):
            # Extract the h3 text and corresponding span text
            if li.find('h3').text.strip() == text:
                return li.find('span', class_='description__job-criteria-text').text.strip()
        return None

    def _extract_seniority_level(self,job_soup: BeautifulSoup) -> str:
        return self._extract_job_criteria_based_on_string(job_soup, "Seniority level")

    def _extract_employment_type(self,job_soup: BeautifulSoup) -> str:
        return self._extract_job_criteria_based_on_string(job_soup, "Employment type")

    def _extract_job_functions(self,job_soup: BeautifulSoup) -> list:
        job_functions = self._extract_job_criteria_based_on_string(job_soup, "Job function")
        return [job_function.strip().replace("and ","") for job_function in job_functions.split(',')]
    
    def _extract_industries(self,job_soup: BeautifulSoup) -> list:
        industries = self._extract_job_criteria_based_on_string(job_soup, "Industries")
        return [industry.strip().replace("and ","") for industry in industries.split(',')]

    

    @staticmethod
    def _extract_job_title(job_soup: BeautifulSoup) -> str:
        """
        Extracts the job title from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Job title text
        """
        return job_soup.find("h2", {"class": "top-card-layout__title font-sans text-lg papabear:text-xl font-bold leading-open text-color-text mb-0 topcard__title"}).text.strip()
        
    @staticmethod
    def _extract_company_name(job_soup: BeautifulSoup) -> str:
        """
        Extracts the company name from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Company name text
        """
        return job_soup.find("a", class_="topcard__org-name-link topcard__flavor--black-link").text.strip()

    @staticmethod
    def _extract_company_url(job_soup: BeautifulSoup) -> str:
        """
        Extracts the company URL from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Company URL text
        """
        return job_soup.find("a", class_="topcard__org-name-link topcard__flavor--black-link")['href'].split("?trk")[0]

    @staticmethod
    def _extract_job_location(job_soup: BeautifulSoup) -> str:
        """
        Extracts the job location from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Job location text
        """
        return job_soup.find("span", class_="topcard__flavor topcard__flavor--bullet").text.strip()
    
    @staticmethod
    def _extract_job_poster(job_soup: BeautifulSoup) -> dict:
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
    def _extract_salary_range(job_soup: BeautifulSoup) -> tuple:
        """
        Extracts the salary range from the job posting page
        :param job_soup: BeautifulSoup object of the job posting page
        :return: Tuple of salary range (low, high)
        """
        salary_range = job_soup.find("div", class_="salary compensation__salary")
        if salary_range:
            # Extract the text and split it into low and high ranges
            salary_text = salary_range.get_text(separator=" ", strip=True)
            # Use regex to extract the numbers from the text
            matches = re.findall(r'\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?', salary_text)
            # if we found two matches, return them as a tuple
            if len(matches) == 2:
                return tuple(int(float(salary.replace('$', '').replace(',', ''))) for salary in matches)
        return None

    @staticmethod
    def _extract_job_description(job_soup: BeautifulSoup) -> str:
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

    def extract_single_job_posting(self,job_id: str) -> JobPosting:
        job_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
        self.logger.info(f"{job_id} - Scraping job")
        retries= 0
        while retries < self.maximum_retries :
            job_request = requests.get(job_url)
            if job_request.status_code == 429:
                wait_time = random.randint(*self.wait_time_limits)
                self.logger.info(f"{job_id} - Too many requests, waiting {wait_time} secs...")
                time.sleep(wait_time)
                retries += 1
                continue
            job_data = job_request.text
            job_soup = BeautifulSoup(job_data, 'html.parser')


            job_poster_info = self._extract_job_poster(job_soup)
            salary_range = self._extract_salary_range(job_soup)

            # You might need to adjust this part based on how you're initializing JobPosting
            job_posting = JobPosting(
                id=job_id,
                title=self._extract_job_title(job_soup),
                seniority_level=self._extract_seniority_level(job_soup),
                employment_type=self._extract_employment_type(job_soup),
                job_description=self._extract_job_description(job_soup),
                company=self._extract_company_name(job_soup),
                company_url=self._extract_company_url(job_soup),
                job_salary_range_min=salary_range[0] if salary_range else None,
                job_salary_range_max=salary_range[1] if salary_range else None,
                job_poster_profile_url = job_poster_info.get("profile_url", None) if job_poster_info else None,
                job_poster_name = job_poster_info.get("name", None) if job_poster_info else None,
                job_functions=self._extract_job_functions(job_soup),
                industries=self._extract_industries(job_soup)
            )
            self.logger.info(f"{job_id} - Successfully extracted data")
            self.write_job_postings_to_database([job_posting])
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

    def write_job_postings_to_database(self, job_postings: list):
        database = DatabaseManager()
        for job_posting in job_postings:
            if job_posting:
                job_posting_db=JobPostingDBModel(**job_posting.to_dict())
                self.logger.info(f"{job_posting.id} - Adding to database")
                database.upsert_object(job_posting_db,['id'])

