from InsertData.DataBase import MY_CUSTOM_BOT
import requests
from urllib.parse import urlparse, urljoin
from re import search
import validators
import spacy
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance
from io import BytesIO
import pytesseract
import sys
from datetime import datetime

# Image extensions (must appear at end of URL path)
IMAGE_EXTENSIONS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', 
    '.webp', '.ico', '.jfif', '.pjpeg', '.pjp', '.avif'
}

# Comprehensive list of filler words to ignore in keyword extraction
FILLER_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'of', 'to', 'in', 'on', 'at', 'for',
    'with', 'by', 'as', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
    'have', 'has', 'had', 'do', 'does', 'did', 'can', 'could', 'shall',
    'should', 'will', 'would', 'may', 'might', 'must', 'that', 'this',
    'these', 'those', 'there', 'here', 'which', 'what', 'when', 'where',
    'who', 'whom', 'whose', 'how', 'why', 'about', 'above', 'below', 'into',
    'over', 'under', 'after', 'before', 'between', 'from', 'up', 'down',
    'out', 'off', 'through', 'during', 'since', 'until', 'upon', 'than',
    'so', 'such', 'same', 'other', 'another', 'each', 'every', 'all', 'any',
    'both', 'either', 'neither', 'only', 'just', 'also', 'very', 'too', 'much',
    'many', 'more', 'most', 'few', 'some', 'no', 'not', 'nor', 'now', 'then',
    'well', 'like', 'even', 'still', 'back', 'yet', 'again', 'ever', 'never',
    'always', 'often', 'sometimes', 'usually', 'once', 'twice', 'first',
    'last', 'next', 'previous', 'new', 'old', 'good', 'bad', 'high', 'low',
    'big', 'small', 'long', 'short', 'great', 'little', 'own', 'same', 'different'
}

def print_progress(current: int, total: int, start_time: datetime):
    """Display progress bar and estimated time remaining"""
    progress = current / total
    bar_length = 40
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    if current > 0 and elapsed > 0:
        remaining = (elapsed / current) * (total - current)
        time_str = f"ETA: {remaining:.0f}s"
    else:
        time_str = "Calculating..."
    
    sys.stdout.write(
        f"\rProgress: |{bar}| {current}/{total} "
        f"({progress:.0%}) {time_str}"
    )
    sys.stdout.flush()

def is_image_url(url: str) -> bool:
    """Check if URL ends with an image file extension"""
    parsed = urlparse(url)
    path = parsed.path.lower()
    return any(path.endswith(ext) for ext in IMAGE_EXTENSIONS)

def preprocess_image(image: Image.Image) -> Image.Image:
    """Enhance image for better OCR results"""
    image = image.convert('L')  # Grayscale
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    enhancer = ImageEnhance.Sharpness(image)
    return enhancer.enhance(2.0)

def extract_text_from_image_url(image_url: str) -> Optional[str]:
    """Extract text from image URLs ending with image extensions"""
    if not is_image_url(image_url):
        return None
        
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(image_url, headers=headers, timeout=15)
        response.raise_for_status()
        
        img = Image.open(BytesIO(response.content))
        img = preprocess_image(img)
        text = pytesseract.image_to_string(img, config='--oem 3 --psm 6')
        return text.strip() if text.strip() else None
        
    except Exception as e:
        print(f"\nError extracting text from image {image_url}: {e}")
        return None

def get_text_frequencies(text: str, word_list: List[str]) -> Dict[str, int]:
    """Count word frequencies in text"""
    if not text:
        return {}
    text_lower = text.lower()
    return {word.lower(): text_lower.count(word.lower()) for word in word_list}

def get_html_frequencies(url: str, word_list: List[str]) -> Dict[str, int]:
    """Extract word frequencies from HTML pages"""
    try:
        result = {word.lower(): 0 for word in word_list}
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 404:
            return {"error": "404 Not Found"}
            
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'iframe']):
            element.decompose()
        
        text = soup.get_text(separator=' ', strip=True).lower()
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)
        
        for token in doc:
            if token.is_alpha and not token.is_stop:
                lemma = token.lemma_
                if lemma in result:
                    result[lemma] += 1
        
        return result
    
    except Exception as e:
        return {"error": f"Error processing HTML: {str(e)}"}

def extract_keywords(query: str, top_n: int = 10, split_phrases: bool = True) -> List[str]:
    """
    Enhanced keyword extraction with option to split phrases into individual words.
    
    Args:
        query: Input text to process
        top_n: Maximum number of keywords to return
        split_phrases: If True, will split phrases into individual words while keeping phrases
    """
    if not query.strip():
        return []

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(query.lower())
    
    # Parts of speech to consider
    pos_tags = ['NOUN', 'PROPN', 'ADJ', 'VERB']
    excluded_words = FILLER_WORDS | {w.lower() for w in nlp.Defaults.stop_words}
    
    candidates = []
    
    # Process individual tokens
    for token in doc:
        if (token.is_punct or token.is_space or 
            token.text in excluded_words or
            len(token.text) < 2):
            continue
            
        if token.pos_ in pos_tags:
            score = 1.0
            if token.pos_ == 'PROPN': score *= 1.5
            if len(token.text) > 5: score *= 1.2
            candidates.append((token.lemma_, score))
    
    # Process noun phrases
    for chunk in doc.noun_chunks:
        phrase = chunk.text.lower()
        words = phrase.split()
        if (len(words) > 1 and 
            not any(w in excluded_words for w in words)):
            candidates.append((phrase, 2.0))
            if split_phrases:
                for word in words:
                    if (word not in excluded_words and 
                        len(word) >= 2):
                        candidates.append((word, 1.0))  # Lower score for individual words
    
    if not candidates:
        return []
    
    # Aggregate and sort keywords
    keyword_scores: Dict[str, float] = {}
    for word, score in candidates:
        keyword_scores[word] = keyword_scores.get(word, 0) + score
    
    # Sort by score (descending), then by length (descending)
    sorted_keywords = sorted(
        keyword_scores.items(),
        key=lambda x: (-x[1], -len(x[0]), x[0])
    )
    
    # Final selection with deduplication
    final_keywords = []
    seen_words = set()
    
    for kw, _ in sorted_keywords:
        # Add the keyword if none of its words are already included
        if split_phrases:
            kw_words = set(kw.split())
            if not kw_words.intersection(seen_words):
                final_keywords.append(kw)
                seen_words.update(kw_words)
        else:
            if kw not in seen_words:
                final_keywords.append(kw)
                seen_words.add(kw)
        
        if len(final_keywords) >= top_n:
            break
    
    return final_keywords

def can_scrape(url: str, user_agent: str = "*") -> bool:
    """Check robots.txt for scraping permissions"""
    if not validators.url(url):
        return False
    parsed = urlparse(url)
    robots_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", "/robots.txt")
    try:
        response = requests.get(robots_url, timeout=10)
        if response.status_code != 200:
            return True
        current_agent = None
        for line in response.text.splitlines():
            line = line.strip().lower()
            if line.startswith("user-agent:"):
                current_agent = line.split(":")[1].strip()
                if current_agent not in ["*", user_agent.lower()]:
                    current_agent = None
            if current_agent and line.startswith("disallow:"):
                path = line.split(":")[1].strip()
                if path and search(path, parsed.path):
                    return False
    except Exception:
        return True
    return True

def get_page_title(url: str) -> str:
    """Fetch HTML page title with fallback to domain"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else ""
        return title[:500] if title else urlparse(url).netloc
    except Exception:
        return urlparse(url).netloc

def insert_search_results(json_data: Dict, query: str) -> List[str]:
    """Insert search results with robust error handling and schema compatibility"""
    # Validate input data
    if not json_data or not isinstance(json_data, dict):
        print("Error: Invalid JSON data provided")
        return []
    
    if "unique_urls" not in json_data or not isinstance(json_data["unique_urls"], list):
        print("Error: Missing or invalid 'unique_urls' in JSON data")
        return []
    
    if "statistics" not in json_data:
        print("Error: Missing statistics in JSON data")
        return []

    # Extract keywords from query using improved function
    key_words = extract_keywords(query)
    if not key_words:
        print("Warning: No keywords extracted from query")
        return []  # Return early if no keywords
    
    bot_db = MY_CUSTOM_BOT()
    not_found_urls = []
    start_time = datetime.now()
    total_urls = len(json_data["unique_urls"])
    inserted_count = 0
    duplicates_count = 0
    error_count = 0

    try:
        # Begin transaction
        bot_db.begin_transaction()
        
        # Insert search query
        search_query_id = bot_db.query(
            """INSERT INTO SearchQuery 
               (Query, TotalUrls, UniqueUrls, Count_Dups, Count_Ads)
               VALUES (%s, %s, %s, %s, %s)""",
            (query,
             json_data["statistics"].get("total_original_urls", 0),
             json_data["statistics"].get("total_unique_urls", 0),
             json_data["statistics"].get("total_occurrences", 0) - json_data["statistics"].get("total_unique_urls", 0),
             json_data["statistics"].get("total_ads_removed", 0)),
            auto_commit=False
        )
        
        if not search_query_id:
            raise ValueError("Failed to insert search query")

        for i, url_data in enumerate(json_data["unique_urls"], 1):
            try:
                print_progress(i, total_urls, start_time)
                
                # Validate URL data structure
                if not isinstance(url_data, dict) or "url" not in url_data:
                    error_count += 1
                    continue
                
                url = url_data["url"]
                if not url or not isinstance(url, str):
                    error_count += 1
                    continue
                
                # Get title with priority: JSON data > HTML title > domain
                title = url_data.get("title", "")
                url_type = 'IMAGE' if is_image_url(url) else 'HTML'
                
                # Handle search engines with proper validation
                search_engines = url_data.get("source_search_engines", [])
                search_engine = search_engines[0] if search_engines else "unknown"
                if len(search_engine) > 50:
                    search_engine = search_engine[:50]
                
                # Check for existing URL (using URL only, not SearchQueryID)
                existing_url = bot_db.query(
                    """SELECT UrlID, SearchEngine FROM search_urls 
                       WHERE Url = %s LIMIT 1""",
                    (url,),
                    fetch=True
                )
                
                url_id = None
                is_new_url = False
                if existing_url and existing_url[0]:
                    duplicates_count += 1
                    url_id = existing_url[0][0]
                    existing_engine = existing_url[0][1]
                    
                    # Update search engine if missing
                    if not existing_engine:
                        bot_db.query(
                            "UPDATE search_urls SET SearchEngine = %s WHERE UrlID = %s",
                            (search_engine, url_id),
                            auto_commit=False
                        )
                else:
                    # Process new URL
                    is_scrappable = can_scrape(url)
                    keyword_data = {}
                    
                    if is_scrappable:
                        try:
                            parsed_url = urlparse(url)
                            domain = parsed_url.netloc[:255]
                            
                            # Only fetch HTML title if we don't have one from JSON
                            if url_type == 'HTML' and not title:
                                title = get_page_title(url)[:500]
                            
                            # Get keyword frequencies based on content type
                            if url_type == 'HTML':
                                freq_result = get_html_frequencies(url, word_list=key_words)
                                if isinstance(freq_result, dict) and not freq_result.get('error'):
                                    keyword_data = freq_result
                                elif freq_result.get('error') == "404 Not Found":
                                    not_found_urls.append(url)
                            else:  # IMAGE processing
                                extracted_text = extract_text_from_image_url(url)
                                if extracted_text:
                                    keyword_data = get_text_frequencies(extracted_text, key_words)
                        except Exception as e:
                            print(f"\nError processing {url}: {str(e)}")
                            is_scrappable = False
                    
                    # Insert URL record
                    bot_db.query(
                        """INSERT INTO search_urls 
                           (SearchQueryID, SearchEngine, Url, Type, Domain, Title, Description, IsScrappable)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (search_query_id, search_engine, url, url_type, 
                         domain if 'domain' in locals() else urlparse(url).netloc[:255], 
                         title, url_data.get("description", "")[:500], is_scrappable),
                        auto_commit=False
                    )
                    
                    url_id = bot_db.cursor.lastrowid
                    inserted_count += 1
                    is_new_url = True
                
                # Process keywords for both new and existing URLs
                if url_id and key_words:  # Ensure we have keywords to process
                    # For existing URLs, we need to get fresh keyword data
                    if not is_new_url:
                        is_scrappable = can_scrape(url)
                        keyword_data = {}
                        if is_scrappable:
                            try:
                                if url_type == 'HTML':
                                    freq_result = get_html_frequencies(url, word_list=key_words)
                                    if isinstance(freq_result, dict) and not freq_result.get('error'):
                                        keyword_data = freq_result
                                else:
                                    extracted_text = extract_text_from_image_url(url)
                                    if extracted_text:
                                        keyword_data = get_text_frequencies(extracted_text, key_words)
                            except Exception as e:
                                print(f"\nError processing keywords for existing URL {url}: {str(e)}")
                    
                    # Initialize with 0 counts for all keywords if no data was collected
                    if not keyword_data:
                        keyword_data = {kw: 0 for kw in key_words}
                    
                    # Ensure all keywords are present in the data (even with 0 counts)
                    for kw in key_words:
                        if kw not in keyword_data:
                            keyword_data[kw] = 0
                    
                    # Insert/update all keywords (including 0 counts)
                    for keyword, freq in keyword_data.items():
                        content_type = 'IMAGE' if url_type == 'IMAGE' else 'TEXT'
                        try:
                            bot_db.query(
                                """INSERT INTO KeyWords 
                                   (UrlID, KeyWordInSearchQuery, Occurrence, ContentType)
                                   VALUES (%s, %s, %s, %s)
                                   ON DUPLICATE KEY UPDATE 
                                   Occurrence = VALUES(Occurrence),
                                   ContentType = VALUES(ContentType)""",
                                (url_id, keyword[:255], freq, content_type),
                                auto_commit=False
                            )
                        except Exception as e:
                            print(f"\nError inserting keyword '{keyword}' for URL {url}: {str(e)}")
                            error_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"\nError processing URL {url}: {str(e)}")
                continue
        
        # Update duplicate count in SearchQuery
        bot_db.query(
            "UPDATE SearchQuery SET Count_Dups = %s WHERE SearchQueryID = %s",
            (duplicates_count, search_query_id),
            auto_commit=False
        )
        
        bot_db.commit()
        print(f"\n\nInsertion complete. Results:")
        print(f"- Total URLs processed: {total_urls}")
        print(f"- New URLs inserted: {inserted_count}")
        print(f"- Existing URLs processed: {duplicates_count}")
        print(f"- Errors encountered: {error_count}")
        print(f"- 404 Not Found URLs: {len(not_found_urls)}")
        print(f"Total processing time: {(datetime.now() - start_time).total_seconds():.1f} seconds")
        
        if not_found_urls:
            print("\nURLs that returned 404:")
            for url in not_found_urls[:10]:
                print(f"- {url}")
            if len(not_found_urls) > 10:
                print(f"- ...and {len(not_found_urls) - 10} more")
        
    except Exception as e:
        bot_db.rollback()
        print(f"\nTransaction failed: {str(e)}")
        raise
    finally:
        bot_db.close()
    
    return key_words

#prints urls that returned 404
#return key_words from search query