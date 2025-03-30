import json
import urllib.parse
import time
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

def setup_driver(headless=True):
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=chrome_options
    )
    return driver

def clean_text(text):
    """Clean text by removing unwanted characters and prefixes"""
    if not text:
        return text
    
    if '\u00b7' in text:
        text = text.split('\u00b7')[-1].strip()
    
    if '\n' in text:
        text = text.split('\n')[-1].strip()
    
    return text

def scrape_ads_container(driver):
    ads_data = []
    try:
        container = driver.find_element(By.XPATH, '/html/body/div[1]/div[3]/div/div/div[1]/div/div/div/ol[1]')
        ad_items = container.find_elements(By.XPATH, './li')
        
        for ad in ad_items:
            try:
                title = clean_text(ad.find_element(By.XPATH, './/h3').text)
                url = ad.find_element(By.XPATH, './/a').get_attribute('href')
                domain = urlparse(url).netloc
                
                try:
                    description = clean_text(ad.find_element(By.XPATH, './/p').text)
                except:
                    description = None
                
                ads_data.append({
                    "url": url,
                    "domain": domain,
                    "title": title,
                    "description": description
                })
            except Exception as e:
                print(f"Error processing ad item: {e}")
    except Exception as e:
        print(f"Error finding ads container: {e}")
    return ads_data

def scrape_organic_results(driver):
    organic_data = []
    try:
        organic_items = driver.find_elements(By.CSS_SELECTOR, "div.algo-sr")
        
        for item in organic_items:
            try:
                title = clean_text(item.find_element(By.CSS_SELECTOR, "h3.title").text)
                url = item.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                domain = urlparse(url).netloc
                
                try:
                    description = clean_text(item.find_element(By.CSS_SELECTOR, "div.compText").text)
                except:
                    description = None
                
                organic_data.append({
                    "url": url,
                    "domain": domain,
                    "title": title,
                    "description": description
                })
            except Exception as e:
                print(f"Error processing organic result: {e}")
    except Exception as e:
        print(f"Error finding organic results: {e}")
    return organic_data

def get_next_page(driver):
    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "a.next")
        return next_button.get_attribute("href")
    except NoSuchElementException:
        return None

def scrape_yahoo_search(query, num_results=10):
    driver = setup_driver()
    base_url = f"https://search.yahoo.com/search?p={urllib.parse.quote(query)}"
    current_url = base_url
    all_organic = []
    all_ads = []
    
    try:
        while current_url and len(all_organic) < num_results:
            print(f"Scraping page... Current results: {len(all_organic)}/{num_results}")
            driver.get(current_url)
            time.sleep(2)
            
            page_ads = scrape_ads_container(driver)
            all_ads.extend(page_ads)
            
            page_organic = scrape_organic_results(driver)
            
            remaining = num_results - len(all_organic)
            if remaining > 0:
                all_organic.extend(page_organic[:remaining])
            
            current_url = get_next_page(driver)
            time.sleep(1)
        
        # Process ad domains for statistics
        ad_domains = {}
        for ad in all_ads:
            domain = ad["domain"]
            ad_domains[domain] = ad_domains.get(domain, 0) + 1
        
        # Prepare final JSON structure exactly as specified
        results_data = {
            "results": all_organic[:num_results],
            "statistics": {
                "total_urls_found": len(all_organic) + len(all_ads),
                "ad_urls_removed": len(all_ads),
                "ad_urls_details": ad_domains,
                "final_urls_count": len(all_organic[:num_results])
            }
        }
        
        return results_data
    finally:
        driver.quit()
