from typing import List, Dict
from InsertData.DataBase import MY_CUSTOM_BOT

def rank_urls_by_keywords(keywords: List[str]) -> List[Dict]:
    """
    Ranks URLs by keyword occurrences including title and description.
    
    Args:
        keywords: List of keywords to search for
        
    Returns:
        [
            {
                'url_id': int,
                'url': str,
                'title': str,
                'description': str,
                'total_occurrences': int,
                'domain': str,
                'type': str,
                'text_matches': int,
                'image_matches': int,
                'keywords': [
                    {'keyword': str, 'count': int, 'source': 'TEXT'/'IMAGE'}
                ],
                'search_engines': List[str],
                'scrapable': bool
            },
            ...
        ]
    """
    if not keywords:
        return []

    bot_db = MY_CUSTOM_BOT()
    try:
        bot_db.begin_transaction()
        
        # Create temporary table for our keywords
        bot_db.query("""
            CREATE TEMPORARY TABLE temp_keywords (
                keyword VARCHAR(255) PRIMARY KEY
            )
        """, auto_commit=False)
        
        # Insert our search keywords (lowercase for case-insensitive matching)
        for keyword in keywords:
            bot_db.query(
                "INSERT IGNORE INTO temp_keywords VALUES (%s)",
                (keyword.lower(),),
                auto_commit=False
            )
        
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
        """
        
        url_results = bot_db.query(query, fetch=True)
        
        ranked_urls = []
        for row in url_results:
            (url_id, url, title, description, domain, 
             url_type, scrapable, search_engines, total, 
             text_matches, image_matches) = row
            
            # Get individual keyword details for this URL
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
            kw_results = bot_db.query(kw_query, (url_id,), fetch=True)
            
            ranked_urls.append({
                'url_id': url_id,
                'url': url,
                'title': title or "",
                'description': description or "",
                'domain': domain,
                'type': url_type,
                'scrapable': bool(scrapable),
                'search_engines': search_engines.split(',') if search_engines else [],
                'total_occurrences': total or 0,
                'text_matches': text_matches or 0,
                'image_matches': image_matches or 0,
                'keywords': [
                    {
                        'keyword': kw[0],
                        'count': kw[1],
                        'source': kw[2]
                    } for kw in kw_results
                ]
            })
        
        bot_db.commit()
        return ranked_urls
    
    except Exception as e:
        bot_db.rollback()
        print(f"Error ranking URLs: {str(e)}")
        raise
    finally:
        bot_db.query("DROP TEMPORARY TABLE IF EXISTS temp_keywords", auto_commit=False)
        bot_db.close()

