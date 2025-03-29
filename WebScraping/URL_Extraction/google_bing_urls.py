import re
import json
from urllib.parse import urlparse, urlunparse
import pytesseract
from pdf2image import convert_from_path
from collections import defaultdict

#WebScrapping For Bing & Google 

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

def is_ad_url(line_number, text_lines):
    text = text_lines.split("\n")
    # Extend check to 4 lines before and 1 line after
    start_line = max(0, line_number - 6)  # Check 6 lines before
    end_line = min(len(text_lines), line_number + 6)  # And 6 line after
    for i in range(start_line, end_line+1):
        line = text[i].lower()
        # Common Google, Bing ad indicators
        list_words = line.split(" ")
        for word in list_words:
            if word == "sponsored":
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
    search_engine_pattern = re.compile(r'(google|bing)\.', re.IGNORECASE)

    for img in images:
        text = pytesseract.image_to_string(img)
        lines = text.split("\n")

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
                
                # Store the line number where the URL was found
                line_number = i
                
                # Check if this is an ad URL
                if is_ad_url(line_number, text):
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
                        "description": description,
                        "line_number": line_number  # Added line number to the result
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
search_engine = "duckduckgo"
pdf_path = r"WebScraping\ScreenCaptures\google_page_1.pdf"
output_json_path = r"WebScraping\ScreenCaptures\search_results.json"  # Output as JSON file
matches = extract_search_results(pdf_path, output_json_path)