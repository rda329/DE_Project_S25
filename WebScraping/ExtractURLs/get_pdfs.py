import os
import time
import webbrowser
import pyautogui
import platform

def get_pdfs(query, engine, page, save_dir="WebScraping/ScreenCaptures"):
    # Create directory if it doesn't exist
    os.makedirs(save_dir, exist_ok=True)

    # Generate search URL
    if engine == "google":
        url = f"https://www.google.com/search?q={query}&start={(page-1)*10}"
    elif engine == "bing":
        url = f"https://www.bing.com/search?q={query}&first={(page-1)*10+1}"
    elif engine == "duckduckgo":
        url = f"https://duckduckgo.com/?q={query}&s={(page-1)*30}"
    elif engine == "yahoo":
        url = f"https://search.yahoo.com/search?p={query}&b={(page-1)*10+1}"
    else:
        raise ValueError("Unsupported search engine")

    # Open browser
    webbrowser.open(url, new=2)
    time.sleep(3)  # Wait for page to load

    # OS-specific print shortcut (Ctrl+P / Cmd+P)
    if platform.system() == "Darwin":  # macOS
        pyautogui.hotkey("command", "p")
    else:  # Windows/Linux
        pyautogui.hotkey("ctrl", "p")
    time.sleep(2)

    # Press Enter to choose "Save as PDF"
    pyautogui.press("enter")
    time.sleep(2)

    # Type the full file path (works on both OSes)
    pdf_path = os.path.join(save_dir, f"{engine}_page_{page}.pdf")
    pyautogui.write(os.path.abspath(pdf_path))  # Absolute path ensures correct dir
    time.sleep(1)

    # Press Enter to save
    pyautogui.press("enter")
    time.sleep(2)

    # Close the print dialog (if needed)
    pyautogui.press("esc")

