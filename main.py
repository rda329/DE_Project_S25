from DataBase import MY_CUSTOM_BOT

#Test file

def main():
    bot = MY_CUSTOM_BOT()

    # Insert a new search query and get the SearchQueryID automatically
    search_query_id = bot.query("""
        INSERT INTO SearchQuery (Query, SearchEngine) 
        VALUES (%s, %s)
    """, ("Machine learning in finance", "Google"))

    # Insert a new search URL linked to the above SearchQueryID and get the UrlID automatically
    url_id = bot.query("""
        INSERT INTO search_urls (SearchQueryID, Url, Title) 
        VALUES (%s, %s, %s)
    """, (search_query_id, "https://example.com", "Machine Learning in Finance"))

    # Insert new keywords linked to the above UrlID
    bot.query("""
        INSERT INTO KeyWords (UrlID, KeyWordInSearchQuery, Occurrence) 
        VALUES (%s, %s, %s)
    """, (url_id, "machine learning", 5))

    bot.query("""
        INSERT INTO KeyWords (UrlID, KeyWordInSearchQuery, Occurrence) 
        VALUES (%s, %s, %s)
    """, (url_id, "finance", 3))

    bot.close()


main()
