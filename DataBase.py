import os
from mysql import connector
from dotenv import load_dotenv

class MY_CUSTOM_BOT:
    def __init__(self):
        load_dotenv()
        db_password = os.getenv("DB_PASSWORD") #Update password from .env file
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
                    CREATE TABLE IF NOT EXISTS search_engines (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(255) UNIQUE NOT NULL,
                        base_url TEXT NOT NULL
                    )
                """)

            self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS search_queries (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        query TEXT NOT NULL,
                        search_engine_id INT NOT NULL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (search_engine_id) REFERENCES search_engines(id) ON DELETE CASCADE
                    )
                """)

            self.cursor.execute("""
                    CREATE TABLE IF NOT EXISTS scraped_queries (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        search_query_id INT NOT NULL,
                        url TEXT NOT NULL,
                        title TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (search_query_id) REFERENCES search_queries(id) ON DELETE CASCADE
                    )
                """)

            print("Connected to MySQL and database initialized.")

        except connector.Error as e:
            print(f"Database connection error: {e}")

    def query(self, sql_query, fetch=False):
        """Execute a query, fetch results if needed."""
        try:
            self.cursor.execute(sql_query)

            # If SELECT, fetch results
            if fetch:
                return self.cursor.fetchall()
            else:
                self.database.commit()  # Commit for INSERT, UPDATE, DELETE

        except connector.Error as e:
            print(f"Query execution error: {e}")

    def close(self):
        """Close the database connection."""
        self.cursor.close()
        self.database.close()
        print("Database connection closed.")