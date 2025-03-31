import json
from collections import defaultdict
import os

def consolidate_search_results():
    """Consolidates search results from multiple search engine JSON files,
    preserving URLs, their sources, one title, one description, and statistics. Removes duplicates"""
    
    folder_path = os.path.join("WebScraping", "URL_JSON")
    
    # Get all JSON files in the folder
    search_engine_files = [
        os.path.join(folder_path, f)
        for f in os.listdir(folder_path)
        if f.endswith("_results.json")
    ]

    url_info = defaultdict(lambda: {
        "search_engines": [],
        "title": None,        # Store only one title
        "description": None, # Store only one description
        "domain": None,      # Store only one domain
        "count": 0
    })
    
    total_stats = {
        "total_ads_removed": 0,
        "total_original_urls": 0,
        "total_unique_urls": 0,
        "total_occurrences": 0,
        "files_processed": []
    }

    for engine_file in search_engine_files:
        try:
            with open(engine_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Update statistics
                total_stats["total_ads_removed"] += data.get("statistics", {}).get("ad_urls_removed", 0)
                total_stats["total_original_urls"] += data.get("statistics", {}).get("total_urls_found", 0)
                total_stats["files_processed"].append(os.path.basename(engine_file))
                
                # Process each search result
                for result in data.get("results", []):
                    if url := result.get("url", ""):
                        engine_name = os.path.basename(engine_file).replace("_results.json", "")
                        
                        # Add engine to sources if not already present
                        if engine_name not in url_info[url]["search_engines"]:
                            url_info[url]["search_engines"].append(engine_name)
                        
                        # Store only the first title encountered
                        if url_info[url]["title"] is None:
                            url_info[url]["title"] = result.get("title")
                        
                        # Store only the first description encountered
                        if url_info[url]["description"] is None:
                            url_info[url]["description"] = result.get("description")
                            
                        # Store only the first domain encountered
                        if url_info[url]["domain"] is None:
                            url_info[url]["domain"] = result.get("domain")
                            
                        url_info[url]["count"] += 1
                        
        except FileNotFoundError:
            print(f"Warning: File {engine_file} not found. Skipping.")
        except json.JSONDecodeError:
            print(f"Warning: Could not parse {engine_file}. Skipping.")
        except Exception as e:
            print(f"Warning: Error processing {engine_file}: {str(e)}. Skipping.")

    # Prepare the final output with single title and description
    unique_urls = [
        {
            "url": url,
            "title": info["title"],            # Single title
            "domain": info["domain"],          # Single domain
            "source_search_engines": info["search_engines"],
            "description": info["description"], # Single description
            "duplicate_count": info["count"]
        }
        for url, info in url_info.items()
    ]

    total_stats["total_unique_urls"] = len(unique_urls)
    total_stats["total_occurrences"] = sum(info["count"] for info in url_info.values())

    return {
        "unique_urls": unique_urls,
        "statistics": total_stats
    }