from WebScraping.scrape import scrape_web
from InsertData.consolidate_urls import consolidate_search_results
from InsertData.insert_url import insert_search_results
from InsertData.url_ranking import rank_urls_by_keywords
from clean_up import delete_files
import time

def run_search(query, num_results):
    scrape_web(query, num_results)
    data = consolidate_search_results()
    key_words = insert_search_results(data, query)
    print("\n\nKey Words",key_words,"\n")
    results = rank_urls_by_keywords(key_words)

    folder_paths = [
        r"WebScraping\URL_JSON",
        r"WebScraping\ScreenCaptures"
    ]

    for folder in folder_paths:
        delete_files(folder)

    return results

def main():
    query ="dogs doing funny things"
    num_results = 5
    start_time = time.time()
    results = run_search(query, num_results) #number of results per search engine
    end_time = time.time()
    print(f"Scrape took {end_time-start_time:.2f} seconds")

    top_10 = results[:3]  # Get first 10 results

    for i, result in enumerate(top_10, 1):
        print(f"\n=== Result #{i} ===")
        print(f"URL ID: {result['url_id']}")
        print(f"URL: {result['url']}")
        print(f"Title: {result['title']}")
        print(f"Description: {result['description']}")
        print(f"Domain: {result['domain']}")
        print(f"Type: {result['type']}")
        print(f"Scrapable: {'Yes' if result['scrapable'] else 'No'}")
        print(f"Search Engines: {', '.join(result['search_engines'])}")
        print(f"Total Occurrences: {result['total_occurrences']}")
        print(f"Text Matches: {result['text_matches']}")
        print(f"Image Matches: {result['image_matches']}")
        
        print("\nKeyword Breakdown:")
        for kw in result['keywords']:
            print(f"  - {kw['keyword']}: {kw['count']} ({kw['source']})")
        
        print("-" * 50)  # Separator between results

if __name__ == "__main__":
    main()


#For google bing there is a max_attempt limit for scraping to num_results / 9. 
#This is to deal with scenario of running out of search pages on search engines.

#9 was chosen because searches produce about 10 results per page

#Interacting with computer while scrapping bing/google with crash code 
#this is because of the work around being used it scrape these sites


#URL that return 404 when attempting connection are not inserted in DB

#Count_dups in DB is the amount of scraped urls that already exist in the db