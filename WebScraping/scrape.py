import json
import os
import time
from .ExtractURLs.get_pdfs import get_pdfs
from .ExtractURLs.google_bing_urls import extract_search_results
from .ExtractURLs.kill_chrome import kill_chrome
from .ExtractURLs.duckduckgo_urls import scrape_duckduckgo
from .ExtractURLs.yahoo_urls import scrape_yahoo_search
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def scrape_google_bing(query, engine, page_counter, max_retries=3):
    """Enhanced with retries but same core logic"""
    for attempt in range(max_retries):
        try:
            # Original logic
            get_pdfs(query, engine, page_counter)
            pdf_path = os.path.join("WebScraping", "ScreenCaptures", f"{engine}_page_{page_counter}.pdf")
            output_path = os.path.join("WebScraping", "URL_JSON", f"{engine}_results.json")
            
            # Ensure directories exist
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            extract_search_results(pdf_path, output_path)
            return True
        except Exception as e:
            logging.warning(f"Attempt {attempt + 1} failed for {engine} page {page_counter}: {str(e)}")
            if attempt == max_retries - 1:
                return False
            time.sleep(2)  # Wait before retrying
    return False

def check_number_urls(engine):
    """Original function with added safety checks"""
    json_path = os.path.join("WebScraping", "URL_JSON", f"{engine}_results.json")
    try:
        if os.path.exists(json_path):
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                return data.get('statistics', {}).get('total_urls_found', 0)
        return 0
    except Exception as e:
        logging.error(f"Error reading {json_path}: {str(e)}")
        return 0

def save_to_json(data, filename):
    """Original function with added error handling"""
    try:
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logging.error(f"Error saving to {filename}: {str(e)}")
        return False

def scrape_web(query, num_results):
    """Main function with enhanced reliability but same logic"""
    engines = ["google", "bing"]
    min_results_per_page = 5  # Expected minimum results per page
    max_pages = 10  # Safety limit
    
    # Scrape google and bing with retries
    for engine in engines:
        page_counter = 1
        total_urls = 0
        attempts = 0
        max_attempts = min(max_pages, num_results/min_results_per_page)
        
        while attempts < max_attempts and total_urls < num_results:
            success = scrape_google_bing(query, engine, page_counter)
            attempts += 1
            
            if success:
                current_urls = check_number_urls(engine)
                if current_urls > total_urls:  # Only increment if we got new results
                    total_urls = current_urls
                    page_counter += 1
                time.sleep(2)  # Be polite between requests
            else:
                break  # Move to next engine if scraping fails

    # Clean up browsers
    kill_chrome()
    time.sleep(1)  # Ensure browsers are closed

    # Scrape duckduckgo (original logic)
    try:
        ddg_data = scrape_duckduckgo(query, num_results)
        save_to_json(ddg_data, os.path.join("WebScraping", "URL_JSON", "duckduckgo_results.json"))
    except Exception as e:
        logging.error(f"DuckDuckGo scrape failed: {str(e)}")

    # Scrape yahoo (original logic)
    try:
        yahoo_data = scrape_yahoo_search(query, num_results)
        save_to_json(yahoo_data, os.path.join("WebScraping", "URL_JSON", "yahoo_results.json"))
    except Exception as e:
        logging.error(f"Yahoo scrape failed: {str(e)}")

    return True