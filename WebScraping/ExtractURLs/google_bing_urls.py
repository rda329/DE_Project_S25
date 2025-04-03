import re
import json
import os
from urllib.parse import urlparse, urlunparse
from collections import defaultdict
from pdf2image import convert_from_path
import pytesseract
import platform

def extract_search_results(pdf_path, output_json_path=None):
    """
    Extract search results from a PDF containing search engine results pages (SERPs).
    Handles both organic results and ads, with statistics tracking.
    
    Args:
        pdf_path: Path to the PDF file to process
        output_json_path: Optional path to JSON file to save/merge results
        
    Returns:
        Dictionary containing extracted results and statistics
    """
    # Convert PDF to images and process each page
    if platform.system() == "Darwin":
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
        images = convert_from_path(
            pdf_path,
            poppler_path="/opt/homebrew/bin"  # ← Your actual path
        )
    else:
        images = convert_from_path(pdf_path)
    new_results = []
    new_stats = {
        'total_urls_found': 0,
        'ad_urls_removed': 0,
        'ad_urls_details': defaultdict(int),
        'final_urls_count': 0
    }
    
    # Regular expressions for URL detection and processing
    base_url_pattern = re.compile(r'\bhttps?://(?:www\.)?[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+')
    continuation_pattern = re.compile(r'\s*(?:>|»)\s*')
    search_engine_pattern = re.compile(r'(google|bing|duckduckgo|yahoo)\.', re.IGNORECASE)

    for img in images:
        text = pytesseract.image_to_string(img)
        lines = text.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]
            base_match = base_url_pattern.search(line)
            
            if base_match and not search_engine_pattern.search(line):
                new_stats['total_urls_found'] += 1
                url_start = base_match.start()
                url_parts = [base_match.group(0), '', '', '', '', '']
                remaining_text = line[base_match.end():]
                
                # Handle URL continuations (like path segments separated by >)
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
                if is_ad_url(i, lines):
                    new_stats['ad_urls_removed'] += 1
                    domain = urlparse(normalized_url).netloc
                    new_stats['ad_urls_details'][domain] += 1
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
                    new_results.append({
                        "url": normalized_url,
                        "domain": parsed_url.hostname,
                        "title": title,
                        "description": description
                    })
            i += 1

    new_stats['final_urls_count'] = len(new_results)
    new_stats['ad_urls_details'] = dict(new_stats['ad_urls_details'])
    
    # Prepare output data
    output_data = {
        'results': new_results,
        'statistics': new_stats
    }

    # Handle JSON output file operations
    if output_json_path:
        try:
            if os.path.exists(output_json_path):
                with open(output_json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    
                    if isinstance(existing_data, dict) and 'results' in existing_data:
                        # Merge results
                        combined_results = existing_data['results'] + new_results
                        
                        # Merge statistics
                        combined_stats = {
                            'total_urls_found': existing_data['statistics']['total_urls_found'] + new_stats['total_urls_found'],
                            'ad_urls_removed': existing_data['statistics']['ad_urls_removed'] + new_stats['ad_urls_removed'],
                            'ad_urls_details': defaultdict(int),
                            'final_urls_count': existing_data['statistics']['final_urls_count'] + new_stats['final_urls_count']
                        }
                        
                        # Merge ad URLs details
                        for domain, count in existing_data['statistics']['ad_urls_details'].items():
                            combined_stats['ad_urls_details'][domain] += count
                        for domain, count in new_stats['ad_urls_details'].items():
                            combined_stats['ad_urls_details'][domain] += count
                        
                        combined_stats['ad_urls_details'] = dict(combined_stats['ad_urls_details'])
                        
                        output_data = {
                            'results': combined_results,
                            'statistics': combined_stats
                        }
                    elif isinstance(existing_data, list):
                        output_data = existing_data + [output_data]
        except (json.JSONDecodeError, KeyError):
            pass

        # Write the updated data back to the file
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=4, ensure_ascii=False)
    
    return output_data

def normalize_url(url):
    """
    Normalize URLs by handling special cases and malformations.
    
    Args:
        url: The URL string to normalize
        
    Returns:
        Normalized URL string
    """
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

def is_ad_url(line_number, text_lines):
    """
    Detect if a URL is an advertisement based on surrounding text.
    
    Args:
        line_number: The line number where the URL was found
        text_lines: Either a list of text lines or a single string
        
    Returns:
        True if the URL is an ad, False otherwise
    """
    if isinstance(text_lines, str):
        text = text_lines.split("\n")
    else:
        text = text_lines
    
    # Check surrounding lines for ad indicators
    start_line = max(0, line_number - 6)
    end_line = min(len(text) - 1, line_number + 6)
    
    for i in range(start_line, end_line + 1):
        line = text[i].lower()
        # Common ad indicators across search engines
        ad_indicators = ['sponsored', 'ad', 'ads', 'advertisement', 'promoted']
        if any(indicator in line for indicator in ad_indicators):
            return True
                
    return False

def is_url_like(text):
    """
    Check if text appears to be a URL or URL fragment.
    
    Args:
        text: The text to check
        
    Returns:
        True if the text appears URL-like, False otherwise
    """
    if not text:
        return False
    return bool(re.match(r'(https?://|www\.|\.com|\.org|\.net|/)', text.strip()))

def clean_text(text):
    """
    Clean extracted text by removing unwanted characters and formatting.
    
    Args:
        text: The text to clean
        
    Returns:
        Cleaned text or None if empty after cleaning
    """
    if not text:
        return None
    text = re.sub(r'^(https?://|www\.|\.com|\.org|\.net|/)\s*', '', text.strip())
    text = re.sub(r'[.,;:!?]\s*$', '', text)  # Remove trailing punctuation
    return text if text else None