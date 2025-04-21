import os
import csv
import time
import random
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# CSV file path from the user's request
CSV_FILE_PATH = 'D:\\Projects\\Scoutagent.AI\\data\\olx_kanjirapally_listings.csv'

# URL to scrape from the user's request
URL = 'https://www.99acres.com/search/property/buy?poiLabel=Near%20Me&latitude=9.5748465&search_type=LS&longitude=76.8047255&latlongsearchdistance=3&preference=S&area_unit=1&res_com=R'

def setup_driver(headless=False):
    """Set up and return a configured Chrome WebDriver"""
    chrome_options = Options()
    if headless:
        chrome_options.add_argument('--headless')
    
    # Add additional options to avoid detection
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-infobars')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-browser-side-navigation')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Set user agent to appear as a regular browser
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
    
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute CDP commands to prevent detection
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    })
    
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
        '''
    })
    
    return driver

def extract_property_details(driver):
    """Extract property details from the current page"""
    properties = []
    
    # Wait for property cards to load
    try:
        # Try different selectors for property cards
        selectors = [
            '.srpTuple', 
            '.projectTuple', 
            '.property-tuple',
            '.srpWrap',
            'div[data-label="SEARCH"]',
            'div[data-label="PROPERTY"]',
            '.srp',  # Added more potential selectors
            '.property-card',
            '.property-list-card',
            '.card'
        ]
        
        property_cards = []
        for selector in selectors:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                cards = driver.find_elements(By.CSS_SELECTOR, selector)
                if cards:
                    print(f"Found {len(cards)} property cards with selector: {selector}")
                    property_cards = cards
                    break
            except:
                continue
        
        if not property_cards:
            # Try a more generic approach - look for divs that might be property cards
            print("Using generic approach to find property cards...")
            all_divs = driver.find_elements(By.TAG_NAME, 'div')
            potential_cards = [div for div in all_divs if div.get_attribute('class') and 
                              ('card' in div.get_attribute('class').lower() or 
                               'property' in div.get_attribute('class').lower() or
                               'listing' in div.get_attribute('class').lower() or
                               'srp' in div.get_attribute('class').lower())]
            
            if potential_cards:
                print(f"Found {len(potential_cards)} potential property cards using generic approach")
                property_cards = potential_cards
        
        # Process each property card
        for card in property_cards:
            try:
                property_data = {}
                
                # Extract all text from the card for analysis
                card_text = card.text
                print(f"\nCard text: {card_text[:200]}...")
                
                # Extract title
                try:
                    # Try to find title elements
                    title_elements = card.find_elements(By.TAG_NAME, 'h2')
                    if not title_elements:
                        title_elements = card.find_elements(By.TAG_NAME, 'a')
                    
                    if title_elements:
                        property_data['title'] = title_elements[0].text.strip()
                    else:
                        # Extract title from card text - first line is often the title
                        lines = card_text.split('\n')
                        if lines:
                            property_data['title'] = lines[0].strip()
                except Exception as e:
                    print(f"Error extracting title: {e}")
                
                # Extract price - look for ₹ symbol
                try:
                    if '₹' in card_text:
                        price_text = [line for line in card_text.split('\n') if '₹' in line]
                        if price_text:
                            property_data['price'] = price_text[0].strip()
                    else:
                        # Look for price patterns
                        price_patterns = ['Cr', 'Lac', 'Lacs', 'L', 'K']
                        price_lines = [line for line in card_text.split('\n') 
                                      if any(pattern in line for pattern in price_patterns)]
                        if price_lines:
                            property_data['price'] = price_lines[0].strip()
                except Exception as e:
                    print(f"Error extracting price: {e}")
                
                # Extract location
                try:
                    # Location often follows certain patterns or keywords
                    location_keywords = ['in', 'at', 'near', 'locality', 'area']
                    location_lines = [line for line in card_text.split('\n') 
                                     if any(keyword in line.lower() for keyword in location_keywords)]
                    
                    if location_lines:
                        property_data['location'] = location_lines[0].strip()
                    else:
                        # Try to find location elements by class names
                        location_elements = card.find_elements(By.CSS_SELECTOR, 
                                                             '[class*="location"], [class*="address"], [class*="area"]')
                        if location_elements:
                            property_data['location'] = location_elements[0].text.strip()
                except Exception as e:
                    print(f"Error extracting location: {e}")
                
                # Extract link
                try:
                    link_element = card.find_element(By.TAG_NAME, 'a')
                    property_data['link'] = link_element.get_attribute('href')
                except Exception as e:
                    print(f"Error extracting link: {e}")
                    # Try to find any link in the card
                    all_links = card.find_elements(By.TAG_NAME, 'a')
                    if all_links:
                        property_data['link'] = all_links[0].get_attribute('href')
                
                # Add current date
                property_data['date'] = datetime.now().strftime('%Y-%m-%d')
                
                # Only add properties that have at least title and one more field
                if 'title' in property_data and len(property_data) > 1:
                    properties.append(property_data)
                    print(f"Extracted property: {property_data}")
            except Exception as e:
                print(f"Error processing property card: {e}")
                continue
    
    except Exception as e:
        print(f"Error extracting properties: {e}")
    
    return properties

def save_to_csv(properties, csv_file_path):
    """Save the scraped properties to a CSV file"""
    # Ensure the directory exists
    os.makedirs(os.path.dirname(csv_file_path), exist_ok=True)
    
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['title', 'price', 'location', 'date', 'link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # Write header
        writer.writeheader()
        
        # Write property data
        for prop in properties:
            row = {
                'title': prop.get('title', 'N/A'),
                'price': prop.get('price', 'N/A'),
                'location': prop.get('location', 'N/A'),
                'date': prop.get('date', datetime.now().strftime('%Y-%m-%d')),
                'link': prop.get('link', 'N/A')
            }
            writer.writerow(row)
    
    print(f"Successfully saved {len(properties)} properties to {csv_file_path}")

def main():
    driver = None
    try:
        print("Starting 99acres.com scraper...")
        driver = setup_driver(headless=False)
        
        # Navigate to the URL
        print(f"Navigating to {URL}")
        driver.get(URL)
        
        # Wait for page to load
        time.sleep(random.uniform(8, 12))
        
        # Print page title and URL for debugging
        print(f"Page title: {driver.title}")
        print(f"Current URL: {driver.current_url}")
        
        # Scroll to load dynamic content
        print("Scrolling to load dynamic content...")
        for _ in range(5):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/5 * {})".format(_ + 1))
            time.sleep(random.uniform(1, 2))
        
        # Save page source for debugging
        with open('99acres_debug_page.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("Saved page source to 99acres_debug_page.html for debugging")
        
        # Extract properties
        properties = extract_property_details(driver)
        
        if properties:
            # Save to CSV
            save_to_csv(properties, CSV_FILE_PATH)
            
            # Display statistics
            print(f"\nScraping completed successfully!")
            print(f"Total properties scraped: {len(properties)}")
            
            # Display sample
            print("\nSample of scraped properties:")
            for i, prop in enumerate(properties[:3]):
                print(f"\nProperty {i+1}:")
                for key, value in prop.items():
                    print(f"  {key}: {value}")
        else:
            print("No properties were found. The website structure might have changed or anti-scraping measures might be in place.")
    
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    finally:
        # Close the browser
        if driver:
            driver.quit()
            print("Browser closed")

if __name__ == "__main__":
    main()