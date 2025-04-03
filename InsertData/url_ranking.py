from typing import List, Dict, Tuple
from InsertData.DataBase import MY_CUSTOM_BOT

def rank_urls_by_keywords(keywords: List[str], page_number: int = 1) -> Tuple[List[Dict], int, bool]:
    """
    Ranks URLs by keyword occurrences including title and description with pagination support.
    
    Args:
        keywords: List of keywords to search for
        page_number: Page number to return (1-based), 5 results per page
        
    Returns:
        Tuple containing:
        - List of result dictionaries
        - Total number of pages
        - Boolean indicating if more results are available
    """
    if not keywords:
        return [], 0, False

    # Validate and normalize inputs
    page_number = max(1, int(page_number))
    results_per_page = 5
    offset = (page_number - 1) * results_per_page

    bot_db = MY_CUSTOM_BOT()
    try:
        bot_db.begin_transaction()
        
        # Create temporary keyword table
        bot_db.query("""
            CREATE TEMPORARY TABLE temp_keywords (
                keyword VARCHAR(255) PRIMARY KEY
            )
        """, auto_commit=False)
        
        # Insert keywords with case-insensitive matching
        for keyword in keywords:
            if keyword.strip():  # Skip empty keywords
                bot_db.query(
                    "INSERT IGNORE INTO temp_keywords VALUES (%s)",
                    (keyword.lower().strip(),),
                    auto_commit=False
                )
        
        # Get total count for pagination
        count_query = """
            SELECT COUNT(DISTINCT su.UrlID)
            FROM search_urls su
            JOIN KeyWords kw ON su.UrlID = kw.UrlID
            JOIN temp_keywords tk ON kw.KeyWordInSearchQuery = tk.keyword
        """
        total_results = int(bot_db.query(count_query, fetch=True)[0][0] or 0)
        total_pages = max(1, (total_results + results_per_page - 1) // results_per_page)
        has_more = (page_number * results_per_page) < total_results

        # Main ranking query
        query = """
            SELECT 
                su.UrlID,
                su.Url,
                su.Title,
                su.Description,
                su.Domain,
                su.Type,
                su.IsScrappable,
                su.SearchEngine,
                SUM(kw.Occurrence) AS total_occurrences,
                SUM(CASE WHEN kw.ContentType = 'TEXT' THEN kw.Occurrence ELSE 0 END) AS text_matches,
                SUM(CASE WHEN kw.ContentType = 'IMAGE' THEN kw.Occurrence ELSE 0 END) AS image_matches
            FROM search_urls su
            JOIN KeyWords kw ON su.UrlID = kw.UrlID
            JOIN temp_keywords tk ON kw.KeyWordInSearchQuery = tk.keyword
            GROUP BY 
                su.UrlID, su.Url, su.Title, su.Description, 
                su.Domain, su.Type, su.IsScrappable, su.SearchEngine
            ORDER BY total_occurrences DESC
            LIMIT %s OFFSET %s
        """
        
        url_results = bot_db.query(query, (results_per_page, offset), fetch=True) or []
        
        # Adjust has_more if we got fewer results than requested
        if len(url_results) < results_per_page:
            has_more = False
        
        # Process results with type safety
        ranked_urls = []
        for row in url_results:
            try:
                (url_id, url, title, description, domain, 
                 url_type, scrapable, search_engines, total, 
                 text_matches, image_matches) = row
                
                # Get keyword details
                kw_query = """
                    SELECT 
                        KeyWordInSearchQuery, 
                        Occurrence, 
                        ContentType
                    FROM KeyWords
                    WHERE UrlID = %s
                    AND KeyWordInSearchQuery IN (
                        SELECT keyword FROM temp_keywords
                    )
                    ORDER BY Occurrence DESC
                """
                kw_results = bot_db.query(kw_query, (url_id,), fetch=True) or []
                
                # Ensure numeric values
                total = int(total) if total is not None else 0
                text_matches = int(text_matches) if text_matches is not None else 0
                image_matches = int(image_matches) if image_matches is not None else 0
                
                ranked_urls.append({
                    'url_id': int(url_id),
                    'url': str(url or ""),
                    'title': str(title or ""),
                    'description': str(description or ""),
                    'domain': str(domain or ""),
                    'type': str(url_type or ""),
                    'scrapable': bool(scrapable),
                    'search_engines': [str(se) for se in (search_engines.split(',') if search_engines else [])],
                    'total_occurrences': total,
                    'text_matches': text_matches,
                    'image_matches': image_matches,
                    'keywords': [{
                        'keyword': str(kw[0] or ""),
                        'count': int(kw[1] or 0),
                        'source': str(kw[2] or "")
                    } for kw in kw_results]
                })
            except Exception as e:
                print(f"Error processing result row: {e}")
                continue
        
        bot_db.commit()
        return ranked_urls, total_pages, has_more
    
    except Exception as e:
        bot_db.rollback()
        print(f"Error ranking URLs: {str(e)}")
        raise
    finally:
        try:
            bot_db.query("DROP TEMPORARY TABLE IF EXISTS temp_keywords", auto_commit=False)
            bot_db.close()
        except Exception as e:
            print(f"Error during cleanup: {str(e)}")