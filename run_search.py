from typing import List, Dict, Tuple
import time
from WebScraping.scrape import scrape_web
from InsertData.consolidate_urls import consolidate_search_results
from InsertData.insert_url import insert_search_results, extract_keywords
from InsertData.url_ranking import rank_urls_by_keywords
from clean_up import delete_files

# Constants
RESULTS_PER_ENGINE = 10  # Number of results to scrape from each engine
NUM_ENGINES = 4          # Number of search engines being used
RESULTS_PER_PAGE = 5     # Number of results to show per page

def run_search(query: str, results_per_engine: int) -> Tuple[float, List[str]]:
    """
    Execute comprehensive search pipeline and return scrape time and keywords.
    
    Args:
        query: Search query string
        results_per_engine: Number of results to scrape from each engine
        
    Returns:
        Tuple of (scrape_time, extracted_keywords)
    """
    start_time = time.time()
    
    # Execute search pipeline (scrapes results_per_engine from each engine)
    scrape_web(query, results_per_engine)
    data = consolidate_search_results()
    keywords = insert_search_results(data, query)
    
    # Calculate duration
    scrape_time = round(time.time() - start_time, 2)
    
    # Clean up files
    for folder in [r"WebScraping\URL_JSON", r"WebScraping\ScreenCaptures"]:
        delete_files(folder)
    
    return scrape_time, keywords

def get_results(query: str, page_number: int = 1) -> Tuple[List[Dict], int, bool]:
    """
    Get paginated ranked results for a search query.
    
    Args:
        query: Search query string
        page_number: Page number to retrieve (1-based)
        
    Returns:
        Tuple of (results, total_pages, has_more)
    """
    keywords = extract_keywords(query)
    results, total_pages, has_more = rank_urls_by_keywords(keywords, page_number)
    return results, total_pages, has_more

def get_initial_results(query: str) -> Tuple[List[Dict], int, float]:
    """
    Get initial search results with comprehensive scraping.
    
    Args:
        query: Search query string
        
    Returns:
        Tuple of (first_page_results, total_pages, scrape_time)
    """
    # Run comprehensive search (scrapes RESULTS_PER_ENGINE from each of NUM_ENGINES)
    scrape_time, _ = run_search(query, RESULTS_PER_ENGINE)
    
    # Get first page of ranked results
    first_page_results, total_pages, _ = get_results(query, 1)
    
    return first_page_results, total_pages, scrape_time

def get_additional_results(query: str, page_number: int) -> Tuple[List[Dict], bool]:
    """
    Get additional results without re-scraping (for Load More functionality).
    
    Args:
        query: Search query string
        page_number: Page number to retrieve
        
    Returns:
        Tuple of (page_results, has_more)
    """
    page_results, _, has_more = get_results(query, page_number)
    return page_results, has_more


#For google bing there is a max_attempt limit for scraping to num_results / 9. 
#This is to deal with scenario of running out of search pages on search engines.

#9 was chosen because searches produce about 10 results per page

#Interacting with computer while scrapping bing/google with crash code 
#this is because of the work around being used it scrape these sites


#URL that return 404 when attempting connection are not inserted in DB

#Count_dups in DB is the amount of scraped urls that already exist in the db