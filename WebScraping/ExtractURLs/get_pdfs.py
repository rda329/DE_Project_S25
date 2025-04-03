import os
import time
import webbrowser
import pyautogui
import platform
import logging

def get_pdfs(query, engine, page, save_dir="WebScraping/ScreenCaptures"):
    """
    Improved version with better error handling and reliability
    while maintaining the original logic flow.
    """
    try:
        # Validate inputs
        if not query or not isinstance(query, str):
            raise ValueError("Invalid search query")
        if engine not in ["google", "bing", "duckduckgo", "yahoo"]:
            raise ValueError("Unsupported search engine")
        if not isinstance(page, int) or page < 1:
            raise ValueError("Page number must be positive integer")

        # Create directory if it doesn't exist
        os.makedirs(save_dir, exist_ok=True)

        # Generate search URL (original logic)
        url = None
        if engine == "google":
            url = f"https://www.google.com/search?q={query}&start={(page-1)*10}"
        elif engine == "bing":
            url = f"https://www.bing.com/search?q={query}&first={(page-1)*10+1}"
        elif engine == "duckduckgo":
            url = f"https://duckduckgo.com/?q={query}&s={(page-1)*30}"
        elif engine == "yahoo":
            url = f"https://search.yahoo.com/search?p={query}&b={(page-1)*10+1}"

        # Open browser with timeout handling
        webbrowser.open(url, new=2)
        start_time = time.time()
        while time.time() - start_time < 10:  # 10 second timeout
            try:
                if pyautogui.getActiveWindowTitle():
                    break
            except:
                pass
            time.sleep(1)
        else:
            raise TimeoutError("Browser didn't open in time")

        # Wait for page to load (with more precise waiting)
        time.sleep(3)

        # OS-specific print handling (original logic)
        if platform.system() == "Darwin":  # macOS
            save_dir = "/Users/rubielaquino/Documents/GitHub/DE_Project_S25/WebScraping/ScreenCaptures/"
            time.sleep(0.5)
            pyautogui.click()
            pyautogui.hotkey("command", "p")
        else:  # Windows/Linux
            pyautogui.hotkey("ctrl", "p")
        time.sleep(1)

        # Save as PDF (original logic with safeguards)
        pdf_path = os.path.join(save_dir, f"{engine}_page_{page}.pdf")
        
        # Remove existing file if it exists
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

        pyautogui.press("enter")  # Select PDF option
        time.sleep(3)

        # Type filename (platform-specific as original)
        if platform.system() == "Darwin":
            pyautogui.write(f"{engine}_page_{page}.pdf")
        else:
            pyautogui.write(os.path.abspath(pdf_path))
        time.sleep(3)
        
        # Finalize save
        pyautogui.press("enter")
        time.sleep(0.5)

        # Verify PDF was created
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF not created at {pdf_path}")

        return True

    except Exception as e:
        # Emergency cleanup - try to close any open dialogs
        try:
            pyautogui.press("esc", presses=3, interval=0.5)
        except:
            pass
        
        logging.error(f"Error in get_pdfs: {str(e)}")
        raise  # Re-raise the exception after cleanup