import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urlparse, parse_qs, unquote
import time
import random
import re

def clean_title(title):
    """
    Removes URL fragments from titles like "www.example.com · path · to · page"
    """
    if not title:
        return None
    # Remove common URL patterns from titles
    cleaned = re.sub(r'\b(www\.|https?:\/\/)?[a-z0-9-]+(\.[a-z]{2,})+\b(\s*·\s*[^\s·]+)*', '', title)
    # Clean up any resulting double spaces or leading/trailing spaces
    cleaned = ' '.join(cleaned.split()).strip()
    return cleaned if cleaned else title  # Return original if cleaning removes everything

def extract_real_url(yahoo_url):
    """
    Extracts the real URL from Yahoo's redirect URL
    """
    try:
        parsed = urlparse(yahoo_url)
        query = parse_qs(parsed.query)
        
        if 'RU' in query:
            return unquote(query['RU'][0])
        
        path_parts = parsed.path.split('/')
        for part in path_parts:
            if part.startswith('RU='):
                return unquote(part[3:])
            
        url_match = re.search(r'RU=([^/]+)', yahoo_url)
        if url_match:
            return unquote(url_match.group(1))
            
    except Exception as e:
        print(f"Error extracting real URL from {yahoo_url}: {e}")
    
    return yahoo_url

def scrape_yahoo(query, num_results=30, max_pages=3):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    base_url = "https://search.yahoo.com/search"
    params = {'p': query, 'b': '1'}
    
    results = []
    ad_urls = {}
    excluded_urls = []
    line_counter = 1
    page = 1
    position = 1
    
    try:
        while len(results) < num_results and page <= max_pages:
            print(f"Fetching page {page} starting at position {position}...")
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            search_results = soup.find_all('div', class_='algo')
            sponsored_results = soup.find_all('li', class_='ads-listing')
            
            if not search_results and not sponsored_results:
                print("No results found, ending scrape")
                break
                
            # Process organic results
            for result in search_results:
                if len(results) >= num_results:
                    break
                    
                title_elem = result.find('h3', class_='title')
                if not title_elem:
                    excluded_urls.append({
                        'reason': 'missing_title_element',
                        'line_number': line_counter,
                        'page_number': page
                    })
                    line_counter += 1
                    position += 1
                    continue
                    
                link = title_elem.find('a')
                if not link:
                    excluded_urls.append({
                        'reason': 'missing_link_element',
                        'line_number': line_counter,
                        'page_number': page
                    })
                    line_counter += 1
                    position += 1
                    continue
                    
                yahoo_url = link.get('href')
                if not yahoo_url:
                    excluded_urls.append({
                        'reason': 'missing_url',
                        'line_number': line_counter,
                        'page_number': page,
                        'title': clean_title(link.text.strip()) if link.text else None
                    })
                    line_counter += 1
                    position += 1
                    continue
                    
                real_url = extract_real_url(yahoo_url)
                domain = urlparse(real_url).netloc
                title = clean_title(link.text.strip()) if link.text else None
                desc_elem = result.find('div', class_='compText')
                description = desc_elem.text.strip() if desc_elem else None
                
                if any(r['url'] == real_url for r in results):
                    excluded_urls.append({
                        'reason': 'duplicate_url',
                        'url': real_url,
                        'domain': domain,
                        'title': title,
                        'line_number': line_counter,
                        'page_number': page
                    })
                    line_counter += 1
                    position += 1
                    continue
                    
                results.append({
                    'url': real_url,
                    'domain': domain,
                    'title': title,
                    'description': description,
                    'line_number': line_counter,
                    'page_number': page,
                    'position': position,
                    'type': 'organic',
                    'yahoo_redirect_url': yahoo_url
                })
                
                line_counter += 1
                position += 1
            
            # Process sponsored results (ads)
            for result in sponsored_results:
                title_elem = result.find('h3', class_='title')
                if not title_elem:
                    continue
                    
                link = title_elem.find('a')
                if not link:
                    continue
                    
                yahoo_url = link.get('href')
                if not yahoo_url:
                    continue
                    
                real_url = extract_real_url(yahoo_url)
                domain = urlparse(real_url).netloc
                title = clean_title(link.text.strip()) if link.text else None
                
                ad_urls[domain] = ad_urls.get(domain, 0) + 1
                excluded_urls.append({
                    'reason': 'advertisement',
                    'url': real_url,
                    'domain': domain,
                    'title': title,
                    'line_number': line_counter,
                    'page_number': page,
                    'position': position,
                    'type': 'sponsored',
                    'yahoo_redirect_url': yahoo_url
                })
                
                line_counter += 1
                position += 1
            
            # Pagination logic remains the same
            next_link = soup.find('a', class_='next')
            if not next_link:
                print("No more pages available, ending scrape")
                break
                
            next_url = next_link.get('href')
            if not next_url:
                print("Next page URL not found, ending scrape")
                break
                
            parsed_next = urlparse(next_url)
            next_params = dict(pair.split('=') for pair in parsed_next.query.split('&') if '=' in pair)
            
            if 'b' not in next_params:
                print("Could not determine next page position, ending scrape")
                break
                
            params['b'] = next_params['b']
            page += 1
            
    except Exception as e:
        print(f"Error during scraping: {e}")
    
    stats = {
        'total_urls_found': line_counter - 1,
        'ad_urls_removed': sum(ad_urls.values()),
        'ad_urls_details': ad_urls,
        'final_urls_count': len(results),
        'pages_scraped': page - 1,
        'excluded_urls_count': len(excluded_urls)
    }
    
    output = {
        'results': results,
        'statistics': stats,
        'excluded_urls': excluded_urls,
        'search_engine': 'yahoo',
        'query': query
    }
    
    return output

if __name__ == "__main__":
    search_query = "advertising agencies in NYC"
    data = scrape_yahoo(search_query, num_results=60, max_pages=5)
    
    # Save to JSON file
    with open('yahoo_search_results.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to yahoo_search_results.json")
    print(f"Total results: {len(data['results'])}")
    print(f"Excluded URLs: {len(data['excluded_urls'])}")
    print(f"Pages scraped: {data['statistics']['pages_scraped']}")