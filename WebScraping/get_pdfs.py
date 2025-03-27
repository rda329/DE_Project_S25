import webbrowser
import pyautogui
import time
import os

# Required for 4 search engines (250 URLs each)
# Google, Yahoo, Bing, DuckDuckGo

def get_pdfs(query, engine, page):
    # Create the directory if it doesn't exist
    save_dir = "ScreenCaptures"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    # Set the appropriate URL based on the search engine and page number
    if engine == "google":
        start = (page - 1) * 10
        url = f"https://www.google.com/search?q={query}&start={start}"
    elif engine == "bing":
        first = (page - 1) * 10 + 1
        url = f"https://www.bing.com/search?q={query}&first={first}"
    elif engine == "duckduckgo":
        s = (page - 1) * 30
        url = f"https://duckduckgo.com/?q={query}&s={s}"
    elif engine == "yahoo":
        b = (page - 1) * 10 + 1
        url = f"https://search.yahoo.com/search?p={query}&b={b}"
    else:
        print("Unsupported search engine!")
        return
    
    # Open the URL in the web browser
    webbrowser.open(url, new=2)

    time.sleep(2)  # Wait for the page to load

    # Simulate "Ctrl + P" to open print dialog
    pyautogui.hotkey('ctrl', 'p')
    time.sleep(2)  # Wait for the print dialog to appear
    # Simulate "Enter" to select "Save as PDF"
    pyautogui.press('enter')
    time.sleep(2)

    # Type the PDF file path
    pyautogui.write(f"{engine}_page_{page}.pdf")
    time.sleep(2)

    # Press "Enter" to save the PDF
    print("Saving the PDF...")
    pyautogui.press('enter')


