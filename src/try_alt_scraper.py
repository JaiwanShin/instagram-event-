"""
try_alt_scraper.py - Try general 'apify/instagram-scraper' to get comments
"""
import requests
import json
import time

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
BASE_URL = "https://api.apify.com/v2"

# Target Post Shortcodes
TARGET_POSTS = [
    "DSuGGGvDFB7",
    "DSuGISfjPUk", 
    "DSlsKZGE9KS"
]

def run_scraper():
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    # Using the general instagram-scraper which often handles parsing better
    actor_id = "apify~instagram-scraper"
    
    direct_urls = [f"https://www.instagram.com/p/{code}/" for code in TARGET_POSTS]
    
    print(f"Starting alt scraper for {len(direct_urls)} posts...")
    
    input_data = {
        "directUrls": direct_urls,
        "resultsType": "comments",  # Requesting comments specifically
        "resultsLimit": 1000,       # High limit
        "searchType": "url",
        "searchLimit": 1,
    }
    
    resp = requests.post(
        f"{BASE_URL}/acts/{actor_id}/runs",
        headers=headers,
        json=input_data,
        params={"waitForFinish": 300}
    )
    
    if resp.status_code != 201:
        print(f"Error: {resp.status_code} {resp.text}")
        return
        
    run_data = resp.json()["data"]
    run_id = run_data["id"]
    print(f"Run ID: {run_id}")
    
    while True:
        status_resp = requests.get(f"{BASE_URL}/actor-runs/{run_id}", headers=headers)
        status = status_resp.json()["data"]["status"]
        print(f"Status: {status}")
        
        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break
        time.sleep(5)
        
    if status == "SUCCEEDED":
        dataset_id = run_data["defaultDatasetId"]
        items_resp = requests.get(f"{BASE_URL}/datasets/{dataset_id}/items", headers=headers)
        items = items_resp.json()
        print(f"Items found: {len(items)}")
        
        if items:
            # Process and save
            processed = []
            seen = set()
            for item in items:
                # Structure might be different in this scraper
                # usually: { "text": "...", "ownerUsername": "...", ... }
                username = item.get("ownerUsername") or item.get("username") or item.get("owner", {}).get("username")
                
                # Check link to post to ensure it belongs to one of ours
                # item might have 'postUrl' or 'inputUrl'
                
                if username:
                    if username not in seen:
                        seen.add(username)
                        processed.append({
                            "username": username,
                            "comment_text": item.get("text", "") or item.get("content", ""),
                            "tagged_users_count": 0, # Might not be parsed
                            "post_shortcode": "unknown" # Need to map back if possible
                        })
            
            print(f"Unique participants found: {len(processed)}")
            with open("data/raw/comments_alt.json", "w", encoding="utf-8") as f:
                json.dump(processed, f, ensure_ascii=False, indent=2)
            print("Saved to data/raw/comments_alt.json")
    else:
        print(f"Run failed: {status}")

if __name__ == "__main__":
    run_scraper()
