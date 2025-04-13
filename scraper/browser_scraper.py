import time
import random
from typing import List
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from .proxy_manager import ProxyManager

class BrowserScraper:
    def __init__(self, headless: bool = False):
        self.proxy_manager = ProxyManager()
        self.headless = headless
        self.driver = None
        
    def start_browser(self, max_retries: int = 3):
        """Initialize browser with enhanced proxy handling and stealth"""
        for attempt in range(max_retries):
            try:
                edge_options = EdgeOptions()
                
                # Enhanced stealth settings
                edge_options.add_argument("--disable-blink-features=AutomationControlled")
                edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                edge_options.add_experimental_option('useAutomationExtension', False)
                
                # Randomize user agent
                user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(100,115)}.0.0.0 Safari/537.36 Edg/{random.randint(100,115)}.0.0.0"
                edge_options.add_argument(f"user-agent={user_agent}")
                
                # Get validated proxy - only if we have valid proxies available
                proxy = None
                try:
                    proxy = self.proxy_manager.get_valid_proxy()
                except Exception as proxy_err:
                    print(f"Proxy error: {str(proxy_err)}. Continuing without proxy.")
                
                # Configure proxy with timeout settings if available
                if proxy:
                    print(f"Attempt {attempt + 1}: Trying proxy {proxy['http']}")
                    edge_options.add_argument(f'--proxy-server={proxy["http"]}')
                    # Add reasonable timeout settings
                    edge_options.add_argument('--proxy-bypass-list=<-loopback>')
                
                # Headless configuration with additional stealth
                if self.headless:
                    edge_options.add_argument('--headless=new')
                    edge_options.add_argument('--disable-gpu')
                    edge_options.add_argument('--window-size=1920,1080')
                    edge_options.add_argument('--disable-dev-shm-usage')
                    edge_options.add_argument('--no-sandbox')

                # Additional performance settings
                edge_options.add_argument('--disable-extensions')
                edge_options.add_argument('--disable-popup-blocking')
                edge_options.add_argument('--disable-infobars')

                # Launch browser
                self.driver = webdriver.Edge(
                    service=Service(EdgeChromiumDriverManager().install()),
                    options=edge_options
                )

                # Set page load timeout
                self.driver.set_page_load_timeout(30)
                
                # Test connection with multiple fallback URLs
                test_urls = [
                    "https://www.google.com",
                    "https://www.bing.com",
                    "https://www.microsoft.com"
                ]
                
                connection_success = False
                for test_url in test_urls:
                    try:
                        self.driver.get(test_url)
                        WebDriverWait(self.driver, 15).until(
                            EC.presence_of_element_located((By.TAG_NAME, 'body'))
                        )
                        connection_success = True
                        break
                    except Exception as url_err:
                        print(f"Failed to connect to {test_url}: {str(url_err)}")
                        continue

                if connection_success:
                    print("Connection successful")
                    return
                else:
                    raise Exception("Failed to connect to any test URL")
                
            except Exception as e:
                print(f"Connection failed on attempt {attempt + 1}: {str(e)}")
                if self.driver:
                    self.driver.quit()
                
        # Fallback to direct connection if all retries fail
        print("Falling back to direct connection")
        edge_options = EdgeOptions()
        if self.headless:
            edge_options.add_argument('--headless=new')
        self.driver = webdriver.Edge(
            service=Service(EdgeChromiumDriverManager().install()),
            options=edge_options
        )
        
        # Set realistic window size
        self.driver.set_window_size(
            random.randint(1200, 1600),
            random.randint(800, 1000)
        )
        
    def scrape_listings(self, url: str, max_pages: int = 5) -> List[dict]:
        """Scrape listings with enhanced error handling and retries"""
        if not self.driver:
            try:
                self.start_browser(max_retries=5)
            except Exception as e:
                print(f"Failed to start browser: {str(e)}")
                return []
            
        # Initial navigation with randomized delays
        time.sleep(random.uniform(1, 3))

        try:    
            print(f"Navigating to {url}")
            self.driver.get(url)
            # Longer wait time for initial page load
            time.sleep(random.uniform(10, 15))  # Significantly increased wait time
            
            # Print page title and URL for debugging
            print(f"Page title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url}")
            
            # Execute JavaScript to scroll down and ensure content is loaded
            print("Scrolling to load dynamic content...")
            for _ in range(3):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                time.sleep(2)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # Save page source for debugging
            with open('page_source.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            print("Saved page source to page_source.html for debugging")
            
            # Try to find any elements on the page to verify content loaded
            try:
                all_elements = self.driver.find_elements(By.TAG_NAME, 'div')
                print(f"Found {len(all_elements)} div elements on the page")
                
                # Try to find any links on the page
                all_links = self.driver.find_elements(By.TAG_NAME, 'a')
                print(f"Found {len(all_links)} links on the page")
                
                # Print first few links for debugging
                for i, link in enumerate(all_links[:5]):
                    try:
                        print(f"Link {i}: {link.get_attribute('href')} - {link.text}")
                    except:
                        pass
            except Exception as e:
                print(f"Error analyzing page elements: {str(e)}")
        except Exception as e:
            print(f"Failed to load initial URL: {str(e)}")
            return []
        
        # Check for CAPTCHA
        if self._detect_captcha():
            print("CAPTCHA detected! Please solve it manually in the browser window.")
            input("Press Enter after solving CAPTCHA to continue...")

        listings: List[dict] = []
        current_page = 1
        
        while current_page <= max_pages:
            try:
                print(f"Processing page {current_page}")
                # Try multiple selectors for listings - updated with current OLX selectors
                listing_selectors = [
                    '[data-cy="l-card"]',
                    'li[data-aut-id="itemBox"]',
                    'div.IKo3_',
                    'li.EIR5N',
                    'div._2Gr10',  # New OLX card class
                    'div[data-aut-id="itemCard"]',  # Generic item card
                    'div.c22e3',  # Another possible card class
                    'div.ee83c'   # Another possible card class
                ]
                
                found_listings = False
                for selector in listing_selectors:
                    try:
                        # Wait for listings to load with each selector
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        found_listings = True
                        print(f"Found listings with selector: {selector}")
                        break
                    except Exception:
                        continue
                
                if not found_listings:
                    print("Could not find any listings with known selectors")
                    break
                
                # Human-like scrolling
                self._simulate_human_scroll()
                
                # Extract listings
                page_listings = self._extract_page_listings()
                if page_listings:
                    listings.extend(page_listings)
                    print(f"Extracted {len(page_listings)} listings from page {current_page}")
                else:
                    print(f"No listings found on page {current_page}")
                
                # Go to next page if available
                if not self._go_to_next_page():
                    print("No more pages available")
                    break
                    
                current_page += 1
                time.sleep(random.uniform(3, 7))  # Delay between pages
                
            except TimeoutException as te:
                print(f"Timed out waiting for page {current_page}: {str(te)}")
                break
            except Exception as e:
                print(f"Error processing page {current_page}: {str(e)}")
                break
                
        print(f"Scraping completed. Found {len(listings)} listings total.")
        return listings

    def _simulate_human_scroll(self):
        """Simulate human-like scrolling behavior"""
        scroll_pauses = random.randint(3, 7)
        scroll_height = self.driver.execute_script("return document.body.scrollHeight")
        
        for _ in range(scroll_pauses):
            scroll_pos = random.randint(0, scroll_height)
            self.driver.execute_script(f"window.scrollTo(0, {scroll_pos});")
            time.sleep(random.uniform(0.5, 2))
            
    def _detect_captcha(self) -> bool:
        """Check if CAPTCHA is present on current page"""
        try:
            captcha_selectors = [
                'iframe[src*="captcha"]',
                'div.captcha',
                'div#captcha',
                'div.recaptcha',
                'div.h-captcha'
            ]
            return any(self.driver.find_elements(By.CSS_SELECTOR, selector) 
                      for selector in captcha_selectors)
        except Exception:
            return False

    def _extract_page_listings(self) -> List[dict]:
        """Extract listing data from current page with multiple selector fallbacks"""
        page_listings = []
        
        # Try multiple selectors for listing cards - updated with latest OLX selectors
        listing_selectors = [
            '[data-cy="l-card"]',
            'li[data-aut-id="itemBox"]',
            'div.IKo3_',
            'li.EIR5N',
            'div._2Gr10',  # New OLX card class
            'div[data-aut-id="itemCard"]',  # Generic item card
            'div.c22e3',  # Another possible card class
            'div.ee83c',   # Another possible card class
            'li._1DNjI'  # Another possible card class
        ]
        
        listings = []
        for selector in listing_selectors:
            try:
                found_listings = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if found_listings:
                    listings = found_listings
                    print(f"Found {len(listings)} listings with selector: {selector}")
                    break
            except Exception:
                continue
        
        if not listings:
            print("Could not find any listings with known selectors")
            return []
        
        for listing in listings:
            try:
                # Try multiple selectors for title - updated with latest OLX selectors
                title = None
                for title_selector in ['h6', 'span[data-aut-id="itemTitle"]', '.title', '[data-aut-id="itemTitle"]', 'div._1hJph', 'div._2Vp0i', 'div._3V5Q8']:
                    try:
                        title_elem = listing.find_element(By.CSS_SELECTOR, title_selector)
                        if title_elem:
                            title = title_elem.text.strip()
                            break
                    except Exception:
                        continue
                
                # Try multiple selectors for price - updated with latest OLX selectors
                price = None
                for price_selector in ['span[data-aut-id="itemPrice"]', '.price', '[data-aut-id="itemPrice"]', 'span._2Ks63', 'div._89yzn', 'div._3Ycv_', 'div._2xKfz']:
                    try:
                        price_elem = listing.find_element(By.CSS_SELECTOR, price_selector)
                        if price_elem:
                            price = price_elem.text.strip()
                            break
                    except Exception:
                        continue
                
                # Try multiple selectors for location - updated with latest OLX selectors
                location = None
                for location_selector in ['span[data-aut-id="item-location"]', '.location', '[data-aut-id="item-location"]', 'span._2TVI3', 'div._1KOFM', 'div._3V5Q8', 'div._3FcWx']:
                    try:
                        location_elem = listing.find_element(By.CSS_SELECTOR, location_selector)
                        if location_elem:
                            location = location_elem.text.strip()
                            break
                    except Exception:
                        continue
                
                # Try multiple selectors for date - updated with latest OLX selectors
                date = None
                for date_selector in ['span[data-aut-id="item-date"]', '.date', '[data-aut-id="item-date"]', 'span.zLvFQ', 'div._2DGqt', 'div._3etmz', 'span._2aJQV']:
                    try:
                        date_elem = listing.find_element(By.CSS_SELECTOR, date_selector)
                        if date_elem:
                            date = date_elem.text.strip()
                            break
                    except Exception:
                        continue
                
                # Get link - this is usually more reliable
                link = None
                try:
                    link_elem = listing.find_element(By.TAG_NAME, 'a')
                    link = link_elem.get_attribute('href')
                    if link and link.startswith('/'):
                        link = 'https://www.olx.in' + link
                except Exception:
                    pass
                
                # Only add listing if we have at least title and link
                if title and link:
                    page_listings.append({
                        'title': title or "No Title",
                        'price': price or "No Price",
                        'location': location or "No Location",
                        'date': date or "No Date",
                        'link': link
                    })
            except Exception as e:
                print(f"Error extracting listing: {e}")
                continue
                
        return page_listings

    def _go_to_next_page(self) -> bool:
        """Navigate to next page if available with multiple selector fallbacks"""
        # Try multiple selectors for next page button
        next_page_selectors = [
            '[data-cy="page-link-next"]',
            'a[data-aut-id="pagination-next"]',
            'a.next',
            'a.pagination__next',
            'li.next a',
            'a[title="Next"]'
        ]
        
        for selector in next_page_selectors:
            try:
                next_btn = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                print(f"Found next page button with selector: {selector}")
                next_btn.click()
                
                # Wait for page to load after clicking next
                WebDriverWait(self.driver, 15).until(
                    EC.staleness_of(next_btn)
                )
                
                # Additional wait for new page to load
                time.sleep(random.uniform(2, 4))
                return True
            except Exception as e:
                print(f"Next button selector '{selector}' failed: {str(e)}")
                continue
        
        print("No next page button found with any known selector")
        return False
            
    def close(self):
        """Clean up browser instance"""
        if self.driver:
            self.driver.quit()
