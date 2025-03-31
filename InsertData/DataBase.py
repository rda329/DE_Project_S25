import os
from dotenv import load_dotenv
from mysql import connector

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

            self.cursor.execute(
                "CREATE DATABASE IF NOT EXISTS MY_CUSTOM_BOT CHARACTER SET utf8mb4")
            self.cursor.execute("USE MY_CUSTOM_BOT")

            # Create necessary tables with updated schema
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS SearchQuery (
                    SearchQueryID INT AUTO_INCREMENT PRIMARY KEY,
                    Query VARCHAR(1000),
                    TotalUrls INT, 
                    UniqueUrls INT,
                    Count_Dups INT,
                    Count_Ads INT,
                    TimeStamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_urls (
                    UrlID INT AUTO_INCREMENT PRIMARY KEY,
                    SearchQueryID INT,
                    SearchEngine VARCHAR(50),
                    Url VARCHAR(1000),
                    Type ENUM('HTML', 'IMAGE') NOT NULL,
                    Domain VARCHAR(255),
                    Title VARCHAR(500),
                    Description Text,
                    IsScrappable BOOLEAN DEFAULT FALSE,
                    TimeStamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY (SearchQueryID, Url(255)),
                    FOREIGN KEY (SearchQueryID) REFERENCES SearchQuery(SearchQueryID) ON DELETE CASCADE
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS KeyWords (
                    KeyWordID INT AUTO_INCREMENT PRIMARY KEY,
                    UrlID INT,
                    KeyWordInSearchQuery VARCHAR(255),
                    Occurrence INT,
                    ContentType ENUM('TEXT', 'IMAGE') DEFAULT 'TEXT',
                    FOREIGN KEY (UrlID) REFERENCES search_urls(UrlID) ON DELETE CASCADE,
                    UNIQUE KEY unique_keyword_url (UrlID, KeyWordInSearchQuery(255))
                )
            """)
            print("Connected to MySQL and database initialized with updated schema.")

        except connector.Error as e:
            print(f"Database connection error: {e}")
            self.close()
            raise

    def query(self, sql_query, params=None, fetch=False, auto_commit=True):
        """Execute a query, fetch results if needed. Handles automatic foreign key assignments."""
        try:
            self.cursor.execute(sql_query, params)

            # For SELECT queries, fetch and return results
            if fetch:
                return self.cursor.fetchall()

            # For INSERT queries, get the last inserted ID
            last_id = None
            if sql_query.strip().upper().startswith("INSERT"):
                last_id = self.cursor.lastrowid

            # Commit if auto_commit is True
            if auto_commit:
                self.database.commit()

            # Return the last inserted ID for INSERT queries
            if sql_query.strip().upper().startswith("INSERT"):
                return last_id

        except connector.Error as e:
            if auto_commit:
                self.database.rollback()
            print(f"Query execution error: {e}")
            raise

    def begin_transaction(self):
        """Start a transaction"""
        self.database.start_transaction()

    def commit(self):
        """Commit the current transaction"""
        self.database.commit()

    def rollback(self):
        """Rollback the current transaction"""
        self.database.rollback()

    def close(self):
        """Close the database connection."""
        if self.cursor:
            self.cursor.close()
            self.cursor = None
        if self.database and self.database.is_connected():
            self.database.close()
            self.database = None
            print("Database connection closed.")