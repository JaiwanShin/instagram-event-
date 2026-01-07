"""
try_single_post_deep.py - Deep scrape for a single post to debug pagination
"""
import requests
import json
import time

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
BASE_URL = "https://api.apify.com/v2"

# Post 1: DSuGGGvDFB7
SHORTCODE = "DSuGGGvDFB7"

def run_deep_scrape():
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    actor_id = "apify~instagram-comment-scraper"
    
    url = f"https://www.instagram.com/p/{SHORTCODE}/"
    print(f"Deep scraping: {url}")
    
    input_data = {
        "directUrls": [url],
        "resultsLimit": 300,  # Explicitly high
        "resultsType": "comments",
        "searchType": "hashtag", # Irrelevant but cleaning default
        # Sometimes 'maxItems' is used instead of resultsLimit depending on version, valid both
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
        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break
        time.sleep(3)
        
    if status == "SUCCEEDED":
        dataset_id = run_data["defaultDatasetId"]
        items_resp = requests.get(f"{BASE_URL}/datasets/{dataset_id}/items", headers=headers)
        items = items_resp.json()
        print(f"Items found: {len(items)}")
        
        # Save for inspection
        with open("debug_comments.json", "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
    else:
        print(f"Run failed: {status}")

if __name__ == "__main__":
    run_deep_scrape()
