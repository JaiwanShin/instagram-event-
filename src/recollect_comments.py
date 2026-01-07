"""
recollect_comments.py - Dedicated script to collect ALL comments
"""
import requests
import json
import time
from pathlib import Path

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
BASE_URL = "https://api.apify.com/v2"

TARGET_POSTS = [
    "DSuGGGvDFB7",
    "DSuGISfjPUk", 
    "DSlsKZGE9KS"
]

RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

def run_scraper_per_post(shortcode):
    """Run scraper for a SINGLE post to ensure max coverage."""
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    actor_id = "apify~instagram-comment-scraper"
    
    post_url = f"https://www.instagram.com/p/{shortcode}/"
    print(f"\n[Scraping] {post_url}")
    
    input_data = {
        "directUrls": [post_url],
        "resultsLimit": 1000,  # High limit per post
        "includeNestedComments": True, # Ensure we catch replies if they count as entries
    }
    
    url = f"{BASE_URL}/acts/{actor_id}/runs"
    resp = requests.post(
        url,
        headers=headers,
        json=input_data,
        params={"waitForFinish": 300}
    )
    
    if resp.status_code != 201:
        print(f"Error starting scraper: {resp.status_code}")
        return []
    
    run_data = resp.json()["data"]
    run_id = run_data["id"]
    print(f"Run ID: {run_id}")
    
    # Wait
    while True:
        status_url = f"{BASE_URL}/actor-runs/{run_id}"
        status_resp = requests.get(status_url, headers=headers)
        status = status_resp.json()["data"]["status"]
        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            break
        time.sleep(3)
    
    if status == "SUCCEEDED":
        dataset_id = run_data.get("defaultDatasetId")
        items_url = f"{BASE_URL}/datasets/{dataset_id}/items"
        items_resp = requests.get(items_url, headers=headers)
        items = items_resp.json()
        print(f"Found {len(items)} comments")
        return items
    
    return []

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_comments = []
    
    for code in TARGET_POSTS:
        comments = run_scraper_per_post(code)
        for c in comments:
            c["post_shortcode"] = code # Ensure shortcode is attached
            all_comments.append(c)
        time.sleep(2)
    
    # Process
    processed = []
    seen_users = set()
    
    for c in all_comments:
        username = c.get("ownerUsername") or c.get("username") or c.get("owner", {}).get("username")
        if username:
            if username not in seen_users:
                seen_users.add(username)
                processed.append({
                    "username": username,
                    "comment_text": c.get("text", ""),
                    "tagged_users_count": len(c.get("mentions", [])),
                    "post_shortcode": c.get("post_shortcode", "")
                })
    
    print(f"\nTotal unique participants: {len(processed)}")
    
    # Merge with existing if needed, but for now just overwrite "comments_v2.json"
    # to avoid breaking the running script's output file
    with open(RAW_DIR / "comments_v2.json", "w", encoding="utf-8") as f:
        json.dump(processed, f, ensure_ascii=False, indent=2)
    print(f"Saved to {RAW_DIR / 'comments_v2.json'}")

if __name__ == "__main__":
    main()
