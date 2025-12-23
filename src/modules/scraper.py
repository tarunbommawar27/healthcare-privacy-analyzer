"""Web scraper module for extracting privacy policies"""

import time
import requests
from typing import Optional, Dict
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils.logger import get_logger

logger = get_logger()


class PolicyScraper:
    """Scraper for extracting privacy policy text from websites"""

    def __init__(self, config: Dict):
        """
        Initialize scraper with configuration

        Args:
            config: Scraping configuration from config.yaml
        """
        self.config = config
        self.timeout = config.get('timeout', 30)
        self.user_agent = config.get('user_agent', 'Mozilla/5.0')
        self.max_retries = config.get('max_retries', 3)
        self.delay = config.get('delay_between_requests', 2)
        self.use_headless = config.get('use_headless', True)

    def scrape_with_requests(self, url: str) -> Optional[str]:
        """
        Scrape policy using requests library (for static pages)

        Args:
            url: URL of the privacy policy

        Returns:
            Extracted text or None if failed
        """
        headers = {'User-Agent': self.user_agent}

        for attempt in range(self.max_retries):
            try:
                logger.info(f"Scraping {url} with requests (attempt {attempt + 1})")
                response = requests.get(url, headers=headers, timeout=self.timeout)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'lxml')

                # Remove script and style elements
                for element in soup(['script', 'style', 'header', 'footer', 'nav']):
                    element.decompose()

                # Try to find main content
                main_content = (
                    soup.find('main') or
                    soup.find('article') or
                    soup.find('div', {'class': ['policy', 'privacy', 'content']}) or
                    soup.find('body')
                )

                if main_content:
                    text = main_content.get_text(separator='\n', strip=True)
                    logger.info(f"Successfully scraped {len(text)} characters")
                    return text

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay)

        logger.error(f"Failed to scrape {url} after {self.max_retries} attempts")
        return None

    def scrape_with_selenium(self, url: str) -> Optional[str]:
        """
        Scrape policy using Selenium (for dynamic pages)

        Args:
            url: URL of the privacy policy

        Returns:
            Extracted text or None if failed
        """
        driver = None
        try:
            logger.info(f"Scraping {url} with Selenium")

            options = Options()
            if self.use_headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument(f'user-agent={self.user_agent}')

            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(self.timeout)
            driver.get(url)

            # Wait for page to load
            wait_time = self.config.get('wait_for_load', 5)
            time.sleep(wait_time)

            # Try to wait for main content
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            except:
                pass  # Continue anyway if main element not found

            # Get page source and parse
            soup = BeautifulSoup(driver.page_source, 'lxml')

            # Remove unwanted elements
            for element in soup(['script', 'style', 'header', 'footer', 'nav']):
                element.decompose()

            # Extract main content
            main_content = (
                soup.find('main') or
                soup.find('article') or
                soup.find('div', {'class': ['policy', 'privacy', 'content']}) or
                soup.find('body')
            )

            if main_content:
                text = main_content.get_text(separator='\n', strip=True)
                logger.info(f"Successfully scraped {len(text)} characters")
                return text

        except Exception as e:
            logger.error(f"Selenium scraping failed: {str(e)}")
            return None

        finally:
            if driver:
                driver.quit()

    def scrape_policy(self, url: str, use_selenium: bool = False) -> Dict:
        """
        Scrape privacy policy from URL

        Args:
            url: URL of the privacy policy
            use_selenium: Whether to use Selenium instead of requests

        Returns:
            Dictionary containing scraped data and metadata
        """
        logger.info(f"Starting to scrape policy from: {url}")

        if use_selenium:
            text = self.scrape_with_selenium(url)
        else:
            text = self.scrape_with_requests(url)

        result = {
            'url': url,
            'text': text,
            'success': text is not None,
            'length': len(text) if text else 0,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        return result
