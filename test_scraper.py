from scraper.olx_scraper import OlxScraper

def main():
    # Initialize scraper with OLX base URL
    scraper = OlxScraper(
        base_url="https://www.olx.in/kanjirapally_g5462080/q-houses?isSearchCall=true",
        location="kanjirapally"
    )

    
    # Run the scraper for 5 pages
    print("Starting OLX scraping...")
    listings = scraper.get_listings(max_pages=5)
    
    if not listings.empty:
        print(f"Successfully scraped {len(listings)} listings")
    else:
        print("No listings were scraped")

if __name__ == "__main__":
    main()
