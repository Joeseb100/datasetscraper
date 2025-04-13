import json
from scraper.browser_scraper import BrowserScraper

def test_scraper():
    """Test the browser-based OLX scraper"""
    test_url = "https://www.olx.in/kanjirapally_g5462080/q-houses"
    
    scraper = BrowserScraper(headless=True)  # Set headless=False for debugging
    try:
        print("Starting scraping test...")
        listings = scraper.scrape_listings(test_url, max_pages=2)
        
        print(f"Scraped {len(listings)} listings")
        print("Sample listing:", json.dumps(listings[0], indent=2) if listings else "No listings found")
        
        # Save results for inspection
        with open('browser_scraper_results.json', 'w', encoding='utf-8') as f:
            json.dump(listings, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Scraping failed: {e}")
    finally:
        scraper.close()

if __name__ == "__main__":
    test_scraper()
