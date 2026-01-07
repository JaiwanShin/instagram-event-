"""
try_alt_scraper_v2.py - Try general 'apify/instagram-scraper' with CORRECT params
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
    # Using "apify/instagram-scraper" (jaroslav-kuchar/instagram-scraper)
    actor_id = "apify~instagram-scraper"
    
    direct_urls = [f"https://www.instagram.com/p/{code}/" for code in TARGET_POSTS]
    
    print(f"Starting alt scraper v2 for {len(direct_urls)} posts...")
    
    input_data = {
        "directUrls": direct_urls,
        "resultsType": "comments",  # Explicitly ask for comments
        "resultsLimit": 200,        # Expecting ~100+
        # Removing searchType/searchLimit as we are using directUrls
        "addParentData": True,
    }
    
    # Run
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
    
    # Wait
    while True:
        status_resp = requests.get(f"{BASE_URL}/actor-runs/{run_id}", headers=headers)
        status = status_resp.json()["data"]["status"]
        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break
        print(f"Status: {status}")
        time.sleep(5)
        
    if status == "SUCCEEDED":
        dataset_id = run_data["defaultDatasetId"]
        # Fetch items
        items_resp = requests.get(f"{BASE_URL}/datasets/{dataset_id}/items", headers=headers)
        items = items_resp.json()
        print(f"Items found: {len(items)}")
        
        if items:
            processed = []
            seen = set()
            for item in items:
                # 'apify/instagram-scraper' structure for comments
                # might be item['text'], item['ownerUsername']
                # or item['content']
                
                # print sample keys to debug if needed
                # print(item.keys())
                
                username = item.get("ownerUsername") or item.get("username")
                text = item.get("text") or item.get("content") or ""
                
                # Sometimes it returns the POST object if it failed to get comments
                if "caption" in item and "commentsCount" in item:
                    # This is a post object, not a comment
                    continue
                    
                if username and text:
                    # Extract shortcode from 'postUrl' if available
                    post_url = item.get("postUrl", "")
                    shortcode = post_url.split("/p/")[-1].strip("/") if "/p/" in post_url else "unknown"
                    
                    if username not in seen:
                        processed.append({
                            "username": username,
                            "comment_text": text,
                            "tagged_users_count": 0, # approximation
                            "post_shortcode": shortcode
                        })
                        seen.add(username) # simple dedupe for now
            
            print(f"Unique comments extracted: {len(processed)}")
            
            # Save to 'comments.json' directly if successful? 
            # Better save to separate file first
            if len(processed) > 40:
                with open("data/raw/comments_full.json", "w", encoding="utf-8") as f:
                    json.dump(processed, f, ensure_ascii=False, indent=2)
                print("SUCCESS: Saved to data/raw/comments_full.json")
            else:
                print("Still low count.")
    else:
        print(f"Run failed: {status}")

if __name__ == "__main__":
    run_scraper()
