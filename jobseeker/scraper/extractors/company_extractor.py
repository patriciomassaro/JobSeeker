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




from jobseeker.scraper.logger import ExtractorLogger
from jobseeker.scraper.datatypes import Institution,CompanySize

class CompanyExtractor:
    def __init__(self, search_page:str ="https://www.google.com/", log_file_name="scraper.log"):
        self.logger = ExtractorLogger(prefix="LinkedInExtractor", log_file_name=log_file_name).get_logger()
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
            time.sleep(2)
            search_box = driver.find_element(By.NAME, "q")
            search_box.send_keys(company_url)
            search_box.send_keys(Keys.ENTER)
            time.sleep(2)
            for i in range(1, 10):
                result = driver.find_element(By.XPATH, f"(//h3)[{i}]/../../a")
                if "linkedin.com" in result.get_attribute("href"):
                    self.logger.info(f" found {company_url} in search result {i}")
                    result.click()
                    time.sleep(3)
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
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        wait = WebDriverWait(driver, 10)

        # Search for the company on LinkedIn and get the HTML of the company page
        html = self.search_linkedin_company_and_get_html(company_url,driver,wait)
        # Parse the HTML of the company page and return the company details
        if html:
            return Institution(url=company_url, **self.parse_company_html(html))
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
        

if __name__ == "__main__":
    scraper = CompanyExtractor(log_file_name="scraper.log")
    companies = ["www.linkedin.com/company/bairesdev/",
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

    institutions = scraper.process_companies_parallel(companies, max_workers=5)
    for institution in institutions:
        if institution is not None:
            print(institution.to_json()) 
