from DataBase import MY_CUSTOM_BOT

#Test file

def main():
    bot = MY_CUSTOM_BOT()

    # Insert sample data into search_engines
    bot.query("INSERT INTO search_engines (name, base_url) VALUES ('Google', 'https://www.google.com')")

    # Fetch inserted search_engine data
    engines = bot.query("SELECT * FROM search_engines", fetch=True)
    print("Search Engines:", engines)

    # Insert sample data into search_queries
    bot.query(f"INSERT INTO search_queries (query, search_engine_id) VALUES ('Python scraping', {engines[0][0]})")

    # Fetch inserted search_queries data
    queries = bot.query("SELECT * FROM search_queries", fetch=True)
    print("Search Queries:", queries)

    # Insert sample data into scraped_queries
    bot.query(f"INSERT INTO scraped_queries (search_query_id, url, title) VALUES ({queries[0][0]}, 'https://www.example.com', 'Example Title')")

    # Fetch inserted scraped_queries data
    scraped_results = bot.query("SELECT * FROM scraped_queries", fetch=True)
    print("Scraped Queries:", scraped_results)

    # Close connection
    bot.close()

main()
