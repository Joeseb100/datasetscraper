import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
import os
import logging
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from fake_useragent import UserAgent
from scraper.proxy_manager import ProxyManager



# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OlxScraper:
    def __init__(self, base_url, location="kanjirapally"):

        self.base_url = base_url
        self.location = location
        self.proxy_manager = ProxyManager()

        self.ua = UserAgent()
        self.headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.com/'
        }

        self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Setup session with retry logic
        self.session = requests.Session()
        retry_strategy = Retry(
            total=5,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["GET"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        
    def get_listings(self, max_pages=5):
        """
        Scrape property listings from OLX
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            DataFrame with property listings
        """
        all_listings = []
        
        for page in range(1, max_pages + 1):
            # For OLX, we need to adjust the URL format based on the base_url
            if 'q=' in self.base_url:
                url = f"{self.base_url}/page/{page}"
            else:
                url = f"{self.base_url}/page/{page}?q={self.location}"
                
            logger.info(f"Scraping page {page}: {url}")
            
            try:
                # Add a longer timeout and use session for requests
                # Rotate user agent for each request
                self.headers['User-Agent'] = self.ua.random
                
                # Add random delay before request
                time.sleep(random.uniform(1, 3))
                
                response = self.session.get(
                    url, 
                    headers=self.headers, 
                    timeout=60,
                    proxies=self.proxy_manager.get_random_proxy()

                )

                response.raise_for_status()
                
                # Add a delay before processing to avoid overloading the server
                time.sleep(random.uniform(5, 15))
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Try different CSS selectors as OLX might change their structure
                listings = soup.find_all('div', class_='IKo3_')
                if not listings:
                    listings = soup.find_all('li', class_='EIR5N')
                if not listings:
                    listings = soup.find_all('li', attrs={'data-aut-id': 'itemBox'})
                
                if not listings:
                    logger.warning(f"No listings found on page {page}. Stopping.")
                    break
                
                for listing in listings:
                    try:
                        # Try different selectors for title
                        title_elem = listing.find('h6')
                        if not title_elem:
                            title_elem = listing.find('span', attrs={'data-aut-id': 'itemTitle'})
                        title = title_elem.text.strip() if title_elem else "No Title"
                        
                        # Try different selectors for price
                        price_elem = listing.find('span', class_='_2Ks63')
                        if not price_elem:
                            price_elem = listing.find('span', attrs={'data-aut-id': 'itemPrice'})
                        price = price_elem.text.strip() if price_elem else "No Price"
                        
                        # Try different selectors for location
                        location_elem = listing.find('span', class_='_2TVI3')
                        if not location_elem:
                            location_elem = listing.find('span', attrs={'data-aut-id': 'item-location'})
                        location = location_elem.text.strip() if location_elem else "No Location"
                        
                        # Try different selectors for date
                        date_elem = listing.find('span', class_='zLvFQ')
                        if not date_elem:
                            date_elem = listing.find('span', attrs={'data-aut-id': 'item-date'})
                        date = date_elem.text.strip() if date_elem else "No Date"
                        
                        # Get link
                        link_elem = listing.find('a')
                        link = link_elem['href'] if link_elem and 'href' in link_elem.attrs else "No Link"
                        if link.startswith('/'):
                            link = 'https://www.olx.in' + link
                        
                        all_listings.append({
                            'title': title,
                            'price': price,
                            'location': location,
                            'date': date,
                            'link': link
                        })
                    except Exception as e:
                        logger.error(f"Error parsing listing: {e}")
                
                # Add a random delay to avoid being blocked
                time.sleep(random.uniform(10, 20))
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                # Don't break, try the next page
                time.sleep(random.uniform(15, 30))
                continue
        
        # Create DataFrame and save to CSV
        df = pd.DataFrame(all_listings)
        
        if not df.empty:
            # Save to the specific file path requested by the user
            filepath = os.path.join(self.data_dir, f"olx_{self.location}_listings.csv")
            # Also save to the exact path specified by the user
            specific_filepath = "D:\\Projects\\Scoutagent.AI\\data\\olx_kanjirapally_listings.csv"
            df.to_csv(specific_filepath, index=False)
            df.to_csv(filepath, index=False)  # Keep the original save for backward compatibility
            logger.info(f"Saved {len(df)} listings to {specific_filepath} and {filepath}")
        else:
            logger.warning("No listings found.")

        return df
