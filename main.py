import os
import argparse
from scraper.olx_scraper import OlxScraper
from utils.translation import TranslationService

def main():
    parser = argparse.ArgumentParser(description='ScoutAgent.AI - Property Listing Scraper')
    parser.add_argument('--url', type=str, 
                        default='https://www.olx.in/kanjirapally_g5462080/q-houses?isSearchCall=true', 
                        help='Base URL for scraping')
    parser.add_argument('--location', type=str, default='kanjirapally', 
                        help='Location to search for')
    parser.add_argument('--pages', type=int, default=5, 
                        help='Maximum number of pages to scrape')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = OlxScraper(args.url, args.location)
    
    # Run the scraper function to fetch listings
    print("⏳ Scraping listings...")
    listings_df = scraper.get_listings(max_pages=args.pages)
    
    if not listings_df.empty:
        # Initialize translation service
        translator = TranslationService()
        
        # Translate the titles to Malayalam
        print("⏳ Translating listings...")
        for index, row in listings_df.iterrows():
            title_ml = translator.translate_text(row['title'], source='en', target='ml')
            print(f"Title: {row['title']}, Translated: {title_ml}")
            
        print("\n✅ Scraping and Translation Complete!")
    else:
        print("❌ No listings found to translate.")

if __name__ == "__main__":
    main()
