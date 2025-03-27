import time
from datetime import datetime
from DataBase import MY_CUSTOM_BOT
from WebScraping.get_pdfs import get_pdfs
from WebScraping.kill_chrome import kill_chrome


def main():
    query = "dog"
    page = 1
    engines = ["google", "bing", "yahoo", "duckduckgo"]
    for engine in engines:
        get_pdfs(query, engine, page)
    kill_chrome()
    


if __name__ == "__main__":
    main()
