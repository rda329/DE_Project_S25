import json
import os
from .ExtractURLs.get_pdfs import get_pdfs
from .ExtractURLs.google_bing_urls import extract_search_results
from .ExtractURLs.kill_chrome import kill_chrome
from .ExtractURLs.duckduckgo_urls import scrape_duckduckgo
from .ExtractURLs.yahoo_urls import scrape_yahoo_search

# Scrape google_bing
def scrape_google_bing(query, engine, page_counter):
    get_pdfs(query, engine, page_counter)  # results saved in WebScraping/ScreenCaptures
    pdf_path = os.path.join("WebScraping", "ScreenCaptures", f"{engine}_page_{page_counter}.pdf")
    output_path = os.path.join("WebScraping", "URL_JSON", f"{engine}_results.json")
    extract_search_results(pdf_path, output_path)

def check_number_urls(engine):
    json_path = os.path.join("WebScraping", "URL_JSON", f"{engine}_results.json")
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        total_urls = data['statistics']['total_urls_found']
        return total_urls

def save_to_json(data, filename):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def scrape_web(query, num_results):  # scrape AT LEAST num_results
    engines = ["google", "bing"]
    # scrapping google_bing
    page_counter = 1
    attempts = 0
    max_attempts = num_results/9 #max scrape attempt
    for engine in engines:
        while attempts < max_attempts:
            scrape_google_bing(query, engine, page_counter)
            total_urls = check_number_urls(engine)
            attempts+=1
            if total_urls >= num_results:
                break
            else:
                page_counter += 1
        page_counter = 1
        attempts = 0
    kill_chrome()

    # scrapping duckduckgo
    output_file = os.path.join("WebScraping", "URL_JSON", "duckduckgo_results.json")
    data = scrape_duckduckgo(query, num_results)
    save_to_json(data, output_file)

    # scrapping yahoo
    data = scrape_yahoo_search(query, num_results)
    output_file = os.path.join("WebScraping", "URL_JSON", "yahoo_results.json")
    save_to_json(data, output_file)