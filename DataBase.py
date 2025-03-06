import os
from dotenv import load_dotenv
from mysql import connector

#FOR CODE TO WORK MUST CREATE A .env file in same directory with DB = "password of your local db"

class MY_CUSTOM_BOT:
    def __init__(self):
        load_dotenv()
        db_password = os.getenv("DB_PASSWORD")  # Update password from .env file
        try:
            # Establish a persistent database connection
            self.database = connector.connect(
                host="localhost",
                user="root",
                password=db_password
            )
            self.cursor = self.database.cursor()

            # Create and use the database
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS MY_CUSTOM_BOT")
            self.cursor.execute("USE MY_CUSTOM_BOT")

            # Create necessary tables
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS SearchQuery (
                    SearchQueryID INT AUTO_INCREMENT PRIMARY KEY,
                    Query VARCHAR(255),
                    SearchEngine VARCHAR(50),
                    TimeStamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS search_urls (
                    UrlID INT AUTO_INCREMENT PRIMARY KEY,
                    SearchQueryID INT,
                    Url TEXT,
                    Title VARCHAR(255),
                    TimeStamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (SearchQueryID) REFERENCES SearchQuery(SearchQueryID) ON DELETE CASCADE
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

    def query(self, sql_query, params=None, fetch=False, auto_commit=True):
        """Execute a query, fetch results if needed. Handles automatic foreign key assignments."""
        try:
            self.cursor.execute(sql_query, params)  # Use parameters for safety (SQL injection prevention)

            # If it's an INSERT, automatically fetch the last inserted ID for relationships
            if sql_query.strip().upper().startswith("INSERT") and auto_commit:
                # Commit the transaction
                self.database.commit()
                # Fetch the last inserted ID (for foreign key assignments)
                self.cursor.execute("SELECT LAST_INSERT_ID()")
                last_inserted_id = self.cursor.fetchone()[0]
                return last_inserted_id

            # If SELECT, fetch results
            if fetch:
                return self.cursor.fetchall()
            else:
                if auto_commit:
                    self.database.commit()  # Commit for INSERT, UPDATE, DELETE

        except connector.Error as e:
            print(f"Query execution error: {e}")

    def close(self):
        """Close the database connection."""
        self.cursor.close()
        self.database.close()
        print("Database connection closed.")
