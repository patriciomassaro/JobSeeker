import time
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent

from jobseeker.logger import Logger
from jobseeker.scraper.datatypes import Institution,CompanySize
from jobseeker.database.models import Institution as InstitutionDBModel
from jobseeker.database import DatabaseManager

class CompanyExtractor:
    def __init__(self, search_page:str ="https://www.google.com/", log_file_name="scraper.log"):
        self.logger = Logger(prefix="CompanyExtractor", log_file_name=log_file_name).get_logger()
        self.search_page = search_page

    @staticmethod
    def get_location(text: str):
        """Extract the location of the company from the HTML of the company page"""
        location= re.search(r"^(.*?)(?=\s+[\d,]+ followers)", text)
        if location:
            return location.group(0).strip()
        else:
            return None
    
    @staticmethod
    def get_followers(text: str):
        """Extract the number of followers of the company from the HTML of the company page"""
        followers = re.search(r"([\d,]+)(?= followers)", text)

        if followers:
            return int(followers.group(0).replace(',', ''))
        else:
            return None

    @staticmethod
    def get_about(html: BeautifulSoup):
        """Extract the about section of the company from the HTML of the company page"""
        about = html.find('p', class_='break-words whitespace-pre-wrap text-color-text')
        if about:
            return about.get_text(separator=' ', strip=True)
        else:
            return None

    @staticmethod
    def get_company_name(html: BeautifulSoup):
        """Extract the name of the company from the HTML of the company page"""
        company_name = html.find('h1', class_='top-card-layout__title')
        if company_name:
            return company_name.get_text(separator=' ', strip=True)
        else:
            return None

    @staticmethod
    def get_industry(html: BeautifulSoup):
        """Extract the industry of the company from the HTML of the company page"""
        industry = html.find('h2', class_='top-card-layout__headline')
        if industry:
            return industry.get_text(separator=' ', strip=True)
        else:
            return None

    @staticmethod
    def get_website(html: BeautifulSoup):
        """Extract the website of the company from the HTML of the company page"""
        website = html.find('a', class_='link-no-visited-state hover:no-underline')
        if website:
            return website.get_text(separator=' ', strip=True)
        else:
            return None

    @staticmethod
    def get_size(html: BeautifulSoup):
        """Extract the size of the company from the HTML of the company page"""
        div = html.find('div', {"class":"mb-2",'data-test-id': 'about-us__size'})
        if div:
            # Find the 'dd' tag within the located div
            dd = div.find('dd')
            if dd:
                size_text = dd.get_text(strip=True)
                company_size_id = CompanySize.get_id(size_text)
                return company_size_id
        return None

    @staticmethod
    def get_specialties(html: BeautifulSoup)-> list[str]:
        """Extract the specialties of the company from the HTML of the company page"""
        # Find the div by the 'data-test-id'
        div = html.find('div', {"class":"mb-2",'data-test-id': 'about-us__specialties'})

        if div:
            # Find the 'dd' tag within the located div
            dd = div.find('dd')
            if dd:
                specialties_text = dd.get_text(strip=True)
                # Split the text by commas to get a list of specialties
                return [specialty.strip().replace("and ","") for specialty in specialties_text.split(',')]
        return None
                
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
    
    def get_location_and_followers_from_html(self,company_soup: str):
        h3 = company_soup.find('h3', class_='top-card-layout__first-subline font-sans text-md leading-open text-color-text-low-emphasis')
        if h3:
            h3_text = h3.get_text(separator=' ', strip=True)
            location = self.get_location(h3_text)
            followers = self.get_followers(h3_text)
            return location, followers
        else:
            return None, None


    def parse_company_html(self, html: str)-> dict:
        """Parse the HTML of the company page and return the company details"""
        company_soup = BeautifulSoup(html, 'html.parser')
        location, followers = self.get_location_and_followers_from_html(company_soup)
        about = self.get_about(company_soup)
        company_name = self.get_company_name(company_soup)
        industry = self.get_industry(company_soup)
        website = self.get_website(company_soup)
        size = self.get_size(company_soup)
        specialties = self.get_specialties(company_soup)

        return {
            "name": company_name,
            "location": location,
            "about": about,
            "website": website,
            "industry": industry,
            "size": size,
            "specialties": specialties,
            "followers": followers
        }
        
    def search_linkedin_company_and_get_html(self, company_url: str,driver,wait):
        """Search for a company on LinkedIn and return the HTML of the company page
        Why looking for the company linkedin in google? to avoid the linkedin login page
        """

        self.logger.info(f"Searching for {company_url}")
        try:  
            driver.get(self.search_page)
            time.sleep(3)
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(company_url)
            search_box.send_keys(Keys.ENTER)
            time.sleep(3)
            for i in range(1, 10):
                result = driver.find_element(By.XPATH, f"(//h3)[{i}]/../../a")
                if "linkedin.com" in result.get_attribute("href"):
                    self.logger.info(f" found {company_url} in search result {i}")
                    result.click()
                    time.sleep(5)
                    html = driver.page_source
                    return html
                else:
                    if i == 9:
                        self.logger.warning(f"LinkedIn URL not found for {company_url}")
        except Exception as e:
            self.logger.error(f"Error occurred for {company_url}: {e}")
            return None
        finally:
            driver.quit()
    
    def process_company(self, company_url: str) -> Institution:
        user_agent = UserAgent().random
        options = webdriver.ChromeOptions()
        # options.add_argument(f'--user-agent={user_agent}') 
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 10)

        # Search for the company on LinkedIn and get the HTML of the company page
        html = self.search_linkedin_company_and_get_html(company_url,driver,wait)
        # Parse the HTML of the company page and return the company details
        if html:
            institution_db=Institution(url=company_url, **self.parse_company_html(html))
            self.write_companies_to_database([institution_db])
            return institution_db
        else:
            self.logger.error(f"Failed to get HTML for company: {company_url}")
            return None

    def process_companies_parallel(self, company_urls: list[str], max_workers: 10) -> list[Institution]:
        """
        Processes a list of company URLs in parallel, returning a list of Institution objects.
        """
        institutions = []  # This will store the Institution objects or None for failures

        # Use ThreadPoolExecutor to parallelize the process_company calls
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Create a future to URL mapping
            future_to_company_url = {executor.submit(self.process_company, url): url for url in company_urls}
            
            for future in as_completed(future_to_company_url):
                company_url = future_to_company_url[future]
                try:
                    institutions.append(future.result())
                except Exception as exc:
                    self.logger.error(f'Company URL {company_url} generated an exception: {exc}')
                    institutions.append(None)

        return institutions

    def write_companies_to_database(self, companies: list[Institution]):
        database = DatabaseManager()
        for company in companies:
            if company:
                company_db=InstitutionDBModel(**company.to_dict())
                self.logger.info(f"{company.url} - Adding to database")
                database.upsert_object(company_db,['url'])    

if __name__ == "__main__":
    start = time.time()
    extractor = CompanyExtractor(log_file_name="scraper.log")
    companies = ["www.linkedin.com/company/bairesdev",
                 "www.linkedin.com/company/Amazon",
                 "www.linkedin.com/company/Google",
                 "www.linkedin.com/company/Microsoft",
                 "www.linkedin.com/company/Apple",
                 "www.linkedin.com/company/Meta",
                 "www.linkedin.com/company/Netflix",
                 "www.linkedin.com/company/Tesla",
                 "www.linkedin.com/company/Twitter",
                 "www.linkedin.com/company/LinkedIn",
                 "www.linkedin.com/company/Uber"]
    companies = extractor.process_companies_parallel(companies, max_workers=2)
    end = time.time()
    # get the len of non None companies
    companies = [company for company in companies if company]
    print(f"Time taken: {end - start} seconds, got {len(companies)} companies")
    extractor.write_companies_to_database(companies)
