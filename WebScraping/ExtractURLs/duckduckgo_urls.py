import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, urljoin
import time

def scrape_duckduckgo(query, num_results):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    base_url = "https://duckduckgo.com/html/"
    params = {'q': query, 'kl': 'us-en'}
    
    results = []
    ad_urls_removed = 0
    ad_urls_details = {}
    line_counter = 1
    page = 1
    
    try:
        while len(results) < num_results:
            print(f"Fetching page {page}...")  # Debug
            
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.find_all('div', class_='result')
            
            print(f"Found {len(search_results)} results on page {page}")  # Debug
            
            if not search_results:
                print("No results found, ending scrape")
                break
                
            new_results_added = 0
            for result in search_results:
                if len(results) >= num_results:
                    break
                    
                # Ad detection
                is_ad = result.find('span', class_='badge--ad js-badge--ad') is not None
                
                title_elem = result.find('a', class_='result__a')
                if not title_elem:
                    line_counter += 1
                    continue
                    
                url = title_elem.get('href')
                if not url:
                    line_counter += 1
                    continue
                    
                domain = urlparse(url).netloc
                
                if is_ad:
                    ad_urls_removed += 1
                    ad_urls_details[domain] = ad_urls_details.get(domain, 0) + 1
                    line_counter += 1
                    continue
                    
                title = title_elem.text.strip()
                desc_elem = result.find('a', class_='result__snippet')
                description = desc_elem.text.strip() if desc_elem else None
                
                if any(r['url'] == url for r in results):
                    line_counter += 1
                    continue
                    
                results.append({
                    'url': url,
                    'domain': domain,
                    'title': title,
                    'description': description
                })
                new_results_added += 1
                line_counter += 1
            
            if new_results_added == 0 and len(results) < num_results:
                print("No new results added on this page, ending scrape")
                break
                
            # Find the next page button and its parent form
            next_button = soup.find('input', {'type': 'submit', 'class': 'btn btn--alt', 'value': 'Next'})
            if not next_button:
                print("No more pages available, ending scrape")
                break
                
            form = next_button.find_parent('form')
            if not form:
                print("Next button form not found, ending scrape")
                break
                
            # Get all form inputs for the next request
            form_data = {}
            for input_tag in form.find_all('input'):
                if input_tag.get('name'):
                    form_data[input_tag['name']] = input_tag.get('value', '')
            
            # Update params for next request
            params = form_data
            page += 1
            time.sleep(2)  # Be polite with delay between requests
            
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    # Prepare statistics to match the provided structure
    stats = {
        'total_urls_found': line_counter - 1,
        'ad_urls_removed': ad_urls_removed,
        'ad_urls_details': ad_urls_details,
        'final_urls_count': len(results),
        'pages_scraped': page - 1
    }
    
    # Create the final JSON structure matching your example
    output = {
        'results': results,
        'statistics': stats
    }
    
    return output

if __name__ == "__main__":
    search_query = "best smartphones 2025"
    data = scrape_duckduckgo(search_query, 40)
    
    # Save to JSON file
    with open('duckduckgo_phone_results.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
