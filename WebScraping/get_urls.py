import re
import json
from urllib.parse import urlparse, urlunparse
import pytesseract
from pdf2image import convert_from_path
from collections import defaultdict

def normalize_url(url):
    # Find the position of the first colon
    first_colon_index = url.find(':')
    
    # If there's no colon in the URL, return it unchanged
    if first_colon_index == -1:
        return url
    
    # Split the URL into the part before the first colon and the part after
    before_colon = url[:first_colon_index + 1]
    after_colon = url[first_colon_index + 1:]
    
    # Replace all subsequent colons with a slash
    modified_after_colon = after_colon.replace(':', '/')
    
    # Recombine the parts
    modified_url = before_colon + modified_after_colon
    return modified_url

def is_url_like(text):
    """Check if text starts with URL indicators"""
    return bool(re.match(r'(https?://|www\.|\.com|\.org|\.net|/)', text.strip()))

def clean_text(text):
    """Clean text by removing URL indicators and trailing special chars"""
    if not text:
        return None
    text = re.sub(r'^(https?://|www\.|\.com|\.org|\.net|/)\s*', '', text.strip())
    text = re.sub(r'[.,;:!?]\s*$', '', text)  # Remove trailing punctuation
    return text if text else None

def is_ad_url(url):
    """Check if URL is likely an ad based on common patterns"""
    # Common ad domains and patterns
    ad_domains = {
        'doubleclick.net',
        'googleadservices.com',
        'googlesyndication.com',
        'google-analytics.com',
        'adservice.google.com',
        'ads.youtube.com',
        'bingads.microsoft.com',
        'yahooads.yahoo.com',
        'ads.yahoo.com',
        'ad.doubleclick.net',
        'adservice.google.*',  # Wildcard for regional variants
        'amazon-adsystem.com',
        'facebook.com/ads',
        'twitter.com/ads',
        'linkedin.com/ads'
    }
    
    # URL parameters that indicate ads
    ad_params = {
        'utm_source=ad',
        'utm_medium=ad',
        'utm_campaign=ad',
        'utm_term=ad',
        'utm_content=ad',
        'gclid=',  # Google Ads parameter
        'msclkid=',  # Microsoft Advertising
        'fbclid=',  # Facebook Ads
        'dclid='   # Display & Video 360
    }
    
    # Check against known ad domains
    domain = urlparse(url).netloc.lower()
    for ad_domain in ad_domains:
        if ad_domain.endswith('*'):
            if domain.startswith(ad_domain[:-1]):
                return True
        elif domain == ad_domain or domain.endswith('.' + ad_domain):
            return True
    
    # Check for ad parameters in URL
    lower_url = url.lower()
    for param in ad_params:
        if param in lower_url:
            return True
    
    # Check for common ad paths
    ad_paths = ('/ads/', '/ad/', '/advert/', '/advertising/')
    path = urlparse(url).path.lower()
    if any(ad_path in path for ad_path in ad_paths):
        return True
    
    return False

def extract_search_results(pdf_path, output_json_path=None):
    images = convert_from_path(pdf_path)
    results = []
    stats = {
        'total_urls_found': 0,
        'ad_urls_removed': 0,
        'ad_urls_details': defaultdict(int),
        'final_urls_count': 0
    }
    
    base_url_pattern = re.compile(r'\bhttps?://(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+')
    continuation_pattern = re.compile(r'\s*(?:>|»)\s*')
    search_engine_pattern = re.compile(r'(google|bing|yahoo|duckduckgo)\.', re.IGNORECASE)

    for img in images:
        text = pytesseract.image_to_string(img)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        i = 0
        while i < len(lines):
            line = lines[i]
            base_match = base_url_pattern.search(line)
            
            if base_match and not search_engine_pattern.search(line):
                stats['total_urls_found'] += 1
                url_start = base_match.start()
                url_parts = [base_match.group(0), '', '', '', '', '']
                remaining_text = line[base_match.end():]
                
                while True:
                    sep_match = continuation_pattern.match(remaining_text)
                    if not sep_match:
                        break
                    remaining_text = remaining_text[sep_match.end():]
                    path_match = re.match(r'[^\s>»]+', remaining_text)
                    if not path_match:
                        break
                    url_parts[2] = (url_parts[2] + '/' + path_match.group(0)).lstrip('/')
                    remaining_text = remaining_text[path_match.end():]
                
                full_url = urlunparse(url_parts)
                normalized_url = normalize_url(full_url)
                
                # Check if this is an ad URL
                if is_ad_url(normalized_url):
                    stats['ad_urls_removed'] += 1
                    domain = urlparse(normalized_url).netloc
                    stats['ad_urls_details'][domain] += 1
                    i += 1
                    continue
                
                parsed_url = urlparse(normalized_url)
                
                # Get title from next non-URL lines
                title = None
                j = i + 1
                while j < len(lines) and (title is None or is_url_like(title)):
                    if lines[j] and not is_url_like(lines[j]):
                        title = clean_text(lines[j])
                    j += 1
                
                # Get description from next non-URL lines after title
                description = None
                while j < len(lines) and (description is None or is_url_like(description)):
                    if lines[j] and not is_url_like(lines[j]):
                        description = clean_text(lines[j])
                    j += 1
                
                if title or description:
                    results.append({
                        "url": normalized_url,
                        "domain": parsed_url.hostname,
                        "title": title,
                        "description": description
                    })
            i += 1

    stats['final_urls_count'] = len(results)
    stats['ad_urls_details'] = dict(stats['ad_urls_details'])  # Convert defaultdict to regular dict
    
    output_data = {
        'results': results,
        'statistics': stats
    }

    if output_json_path:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    return output_data


#In the regular expression make sure to exclude urls that include the www.google www.bing , etc
#update save results in json struct

# Example usage
pdf_path = r"C:\Users\rubie\Desktop\DE_Project_S25\ScreenCaptures\duckduckgo_page_1.pdf"
output_json_path = "search_results.json"  # Output as JSON file
matches = extract_search_results(pdf_path, output_json_path)