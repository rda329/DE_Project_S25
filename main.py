import time
from datetime import datetime
from DataBase import MY_CUSTOM_BOT

def test_main():
    # Initialize the bot
    print("Initializing MY_CUSTOM_BOT...")
    bot = MY_CUSTOM_BOT()

    try:
        # Test 1: Insert a search query
        print("\nTest 1: Inserting a search query")
        search_query = "python database tutorial"
        search_engine = "Google"
        query_id = bot.query(
            "INSERT INTO SearchQuery (Query, SearchEngine, UniqueUrls, Count_Ads, Count_Dups, Count_Promos) VALUES (%s, %s, %s, %s, %s, %s)",
            (search_query, search_engine, 5, 2, 1, 0)
        )
        print(f"Inserted SearchQuery with ID: {query_id}")

        # Test 2: Insert URLs
        print("\nTest 2: Inserting URLs")
        urls = [
            ("https://www.python.org/doc/tutorial/", "Python Tutorial - Python Documentation", query_id),
            ("https://docs.python.org/3/tutorial/", "The Python Tutorial — Python 3 documentation", query_id),
            ("https://www.w3schools.com/python/", "Python Tutorial - W3Schools", query_id),
            ("https://www.tutorialspoint.com/python/", "Python Tutorial - Tutorialspoint", query_id),
            ("https://realpython.com/tutorials/basics/", "Python Basics Tutorials – Real Python", query_id)
        ]

        url_ids = []
        for url, title, q_id in urls:
            try:
                url_id = bot.query(
                    "INSERT INTO search_urls (SearchQueryID, Url, Title) VALUES (%s, %s, %s)",
                    (q_id, url, title)
                )
                url_ids.append(url_id)
                print(f"Inserted URL: {url} with ID: {url_id}")
            except Exception as e:
                print(f"Failed to insert URL {url}: {e}")

        # Test 3: Test duplicate URL constraint
        print("\nTest 3: Testing duplicate URL constraint")
        try:
            # Try to insert a duplicate URL
            duplicate_url_id = bot.query(
                "INSERT INTO search_urls (SearchQueryID, Url, Title) VALUES (%s, %s, %s)",
                (query_id, urls[0][0], "Duplicate URL Test")
            )
            print("Warning: Duplicate URL was inserted. Unique constraint may not be working.")
        except Exception as e:
            print(f"Expected error for duplicate URL: {e}")

        # Test 4: Insert keywords
        print("\nTest 4: Inserting keywords")
        keywords = [
            (url_ids[0], "python", 12),
            (url_ids[0], "tutorial", 8),
            (url_ids[1], "python", 15),
            (url_ids[1], "tutorial", 10),
            (url_ids[2], "python", 20),
            (url_ids[2], "tutorial", 12)
        ]

        for url_id, keyword, occurrence in keywords:
            keyword_id = bot.query(
                "INSERT INTO KeyWords (UrlID, KeyWordInSearchQuery, Occurrence) VALUES (%s, %s, %s)",
                (url_id, keyword, occurrence)
            )
            print(f"Inserted keyword '{keyword}' with ID: {keyword_id}")

        # Test 5: Query the data
        print("\nTest 5: Querying the data")
        search_queries = bot.query("SELECT * FROM SearchQuery", fetch=True)
        print(f"Search Queries: {search_queries}")

        search_urls = bot.query("SELECT * FROM search_urls", fetch=True)
        print(f"URLs: {search_urls}")

        keywords = bot.query("SELECT * FROM KeyWords", fetch=True)
        print(f"Keywords: {keywords}")

        # Test 6: Complex join query
        print("\nTest 6: Complex join query")
        complex_query = """
        SELECT sq.Query, su.Url, su.Title, kw.KeyWordInSearchQuery, kw.Occurrence
        FROM SearchQuery sq
        JOIN search_urls su ON sq.SearchQueryID = su.SearchQueryID
        JOIN KeyWords kw ON su.UrlID = kw.UrlID
        WHERE kw.Occurrence > 10
        ORDER BY kw.Occurrence DESC
        """

        results = bot.query(complex_query, fetch=True)
        print("Results of complex query:")
        for row in results:
            print(f"Query: {row[0]}, URL: {row[1]}, Title: {row[2]}, Keyword: {row[3]}, Occurrences: {row[4]}")

    except Exception as e:
        print(f"Test error: {e}")
    finally:
        # Clean up - close the database connection
        bot.close()


if __name__ == "__main__":
    test_main()
