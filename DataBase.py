import os
from dotenv import load_dotenv
from mysql import connector


# FOR CODE TO WORK MUST CREATE A .env file in same directory with DB_PASSWORD="your_password"

class MY_CUSTOM_BOT:
    def __init__(self):
        load_dotenv()
        db_password = os.getenv("DB_PASSWORD")

        self.database = None
        self.cursor = None

        try:
            # Establish a persistent database connection
            self.database = connector.connect(
                host="localhost",
                user="root",
                password=db_password,
                charset="utf8mb4"
            )
            self.cursor = self.database.cursor()

            # Create and use the database
            self.cursor.execute(
                "CREATE DATABASE IF NOT EXISTS MY_CUSTOM_BOT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            self.cursor.execute("USE MY_CUSTOM_BOT")

            # Create necessary tables
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS SearchQuery (
                    SearchQueryID INT AUTO_INCREMENT PRIMARY KEY,
                    Query VARCHAR(255),
                    SearchEngine VARCHAR(50),
                    UniqueUrls INT,
                    Count_Ads INT,
                    Count_Dups INT,
                    Count_Promos INT,
                    TimeStamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_urls (
                    UrlID INT AUTO_INCREMENT PRIMARY KEY,
                    SearchQueryID INT,
                    Url VARCHAR(2083),
                    Title VARCHAR(500),
                    TimeStamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (SearchQueryID) REFERENCES SearchQuery(SearchQueryID) ON DELETE CASCADE,
                    UNIQUE KEY unique_url (Url(255))
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS KeyWords (
                    KeyWordID INT AUTO_INCREMENT PRIMARY KEY,
                    UrlID INT,
                    KeyWordInSearchQuery VARCHAR(100),
                    Occurrence INT,
                    FOREIGN KEY (UrlID) REFERENCES search_urls(UrlID) ON DELETE CASCADE
                )
            """)

            print("Connected to MySQL and database initialized.")

        except connector.Error as e:
            print(f"Database connection error: {e}")
            if self.cursor:
                self.cursor.close()
            if self.database and self.database.is_connected():
                self.database.close()
            raise

    def query(self, sql_query, params=None, fetch=False, auto_commit=True):
        """Execute a query, fetch results if needed. Handles automatic foreign key assignments."""
        try:
            self.cursor.execute(sql_query, params)

            # If it's an INSERT, automatically fetch the last inserted ID for relationships
            if sql_query.strip().upper().startswith("INSERT") and auto_commit:
                # Commit the transaction
                self.database.commit()
                # Fetch the last inserted ID (for foreign key assignments)
                last_inserted_id = self.cursor.lastrowid
                return last_inserted_id

            # If SELECT, fetch results
            if fetch:
                return self.cursor.fetchall()
            else:
                if auto_commit:
                    self.database.commit()

        except connector.Error as e:
            if auto_commit:
                self.database.rollback()
            print(f"Query execution error: {e}")
            raise

    def close(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.database and self.database.is_connected():
            self.database.close()
            print("Database connection closed.")