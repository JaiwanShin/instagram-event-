"""
test_apify.py - Test Apify API connection and collect data
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

def test_connection():
    """Test API connection."""
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    resp = requests.get(f"{BASE_URL}/users/me", headers=headers)
    print(f"API Status: {resp.status_code}")
    if resp.status_code == 200:
        user = resp.json()
        print(f"User: {user.get('data', {}).get('username', 'unknown')}")
        return True
    else:
        print(f"Error: {resp.text[:200]}")
        return False

def run_scraper(post_urls):
    """Run Instagram Comment Scraper."""
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    
    # Using apify/instagram-comment-scraper
    actor_id = "apify~instagram-comment-scraper"
    
    input_data = {
        "directUrls": post_urls,
        "resultsLimit": 1000,
    }
    
    print(f"\nStarting scraper for {len(post_urls)} posts...")
    
    url = f"{BASE_URL}/acts/{actor_id}/runs"
    resp = requests.post(
        url,
        headers=headers,
        json=input_data,
        params={"waitForFinish": 300}
    )
    
    if resp.status_code != 201:
        print(f"Error: {resp.status_code}")
        print(resp.text[:500])
        return []
    
    run_data = resp.json()["data"]
    run_id = run_data["id"]
    status = run_data.get("status")
    print(f"Run ID: {run_id}, Status: {status}")
    
    # Wait for completion
    while status not in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
        time.sleep(5)
        status_url = f"{BASE_URL}/actor-runs/{run_id}"
        status_resp = requests.get(status_url, headers=headers)
        if status_resp.status_code == 200:
            status = status_resp.json()["data"]["status"]
            print(f"Status: {status}")
    
    if status != "SUCCEEDED":
        print(f"Run failed with status: {status}")
        return []
    
    # Get results
    dataset_id = run_data.get("defaultDatasetId")
    if not dataset_id:
        print("No dataset found")
        return []
    
    items_url = f"{BASE_URL}/datasets/{dataset_id}/items"
    items_resp = requests.get(items_url, headers=headers)
    
    if items_resp.status_code == 200:
        items = items_resp.json()
        print(f"Retrieved {len(items)} items")
        return items
    
    return []

def collect_profiles(usernames):
    """Collect user profiles."""
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    actor_id = "apify~instagram-profile-scraper"
    
    # Batch usernames (max 50 per run)
    batch_size = 50
    all_profiles = []
    
    for i in range(0, len(usernames), batch_size):
        batch = usernames[i:i+batch_size]
        print(f"\nCollecting profiles batch {i//batch_size + 1}: {len(batch)} users")
        
        input_data = {
            "usernames": batch,
        }
        
        url = f"{BASE_URL}/acts/{actor_id}/runs"
        resp = requests.post(
            url,
            headers=headers,
            json=input_data,
            params={"waitForFinish": 300}
        )
        
        if resp.status_code != 201:
            print(f"Error: {resp.status_code}")
            continue
        
        run_data = resp.json()["data"]
        run_id = run_data["id"]
        status = run_data.get("status")
        
        while status not in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            time.sleep(3)
            status_url = f"{BASE_URL}/actor-runs/{run_id}"
            status_resp = requests.get(status_url, headers=headers)
            if status_resp.status_code == 200:
                status = status_resp.json()["data"]["status"]
        
        if status == "SUCCEEDED":
            dataset_id = run_data.get("defaultDatasetId")
            if dataset_id:
                items_url = f"{BASE_URL}/datasets/{dataset_id}/items"
                items_resp = requests.get(items_url, headers=headers)
                if items_resp.status_code == 200:
                    all_profiles.extend(items_resp.json())
        
        time.sleep(2)
    
    return all_profiles

def collect_user_posts(usernames):
    """Collect posts for users."""
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    actor_id = "apify~instagram-post-scraper"
    
    all_posts = []
    
    for username in usernames[:50]:  # Limit to 50 users
        print(f"Collecting posts for {username}")
        
        input_data = {
            "username": [username],
            "resultsLimit": 12,
        }
        
        url = f"{BASE_URL}/acts/{actor_id}/runs"
        resp = requests.post(
            url,
            headers=headers,
            json=input_data,
            params={"waitForFinish": 120}
        )
        
        if resp.status_code != 201:
            continue
        
        run_data = resp.json()["data"]
        run_id = run_data["id"]
        status = run_data.get("status")
        
        while status not in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            time.sleep(2)
            status_url = f"{BASE_URL}/actor-runs/{run_id}"
            status_resp = requests.get(status_url, headers=headers)
            if status_resp.status_code == 200:
                status = status_resp.json()["data"]["status"]
        
        if status == "SUCCEEDED":
            dataset_id = run_data.get("defaultDatasetId")
            if dataset_id:
                items_url = f"{BASE_URL}/datasets/{dataset_id}/items"
                items_resp = requests.get(items_url, headers=headers)
                if items_resp.status_code == 200:
                    for post in items_resp.json():
                        post["username"] = username
                        all_posts.append(post)
        
        time.sleep(1)
    
    return all_posts

def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("Instagram Data Collection via Apify")
    print("=" * 60)
    
    # Test connection
    if not test_connection():
        print("API connection failed. Exiting.")
        return
    
    # Step 1: Collect comments
    post_urls = [f"https://www.instagram.com/p/{code}/" for code in TARGET_POSTS]
    comments = run_scraper(post_urls)
    
    if not comments:
        print("No comments collected. Using sample data.")
        return
    
    # Process comments
    processed_comments = []
    unique_users = set()
    
    for c in comments:
        username = c.get("ownerUsername") or c.get("username") or c.get("owner", {}).get("username")
        if username:
            unique_users.add(username)
            processed_comments.append({
                "username": username,
                "comment_text": c.get("text", ""),
                "tagged_users_count": len(c.get("mentions", [])),
                "post_shortcode": c.get("postShortCode", c.get("shortcode", ""))
            })
    
    # Deduplicate by username
    seen = set()
    deduped = []
    for c in processed_comments:
        if c["username"] not in seen:
            seen.add(c["username"])
            deduped.append(c)
    
    with open(RAW_DIR / "comments.json", "w", encoding="utf-8") as f:
        json.dump(deduped, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(deduped)} unique comments")
    
    # Step 2: Collect profiles
    usernames = list(unique_users)
    print(f"\nCollecting profiles for {len(usernames)} users...")
    profiles = collect_profiles(usernames)
    
    processed_profiles = []
    for p in profiles:
        processed_profiles.append({
            "username": p.get("username", ""),
            "followers": p.get("followersCount", 0),
            "following": p.get("followsCount", 0),
            "is_private": p.get("isPrivate", False),
            "post_count": p.get("postsCount", 0),
            "bio": p.get("biography", "")
        })
    
    with open(RAW_DIR / "profiles.json", "w", encoding="utf-8") as f:
        json.dump(processed_profiles, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(processed_profiles)} profiles")
    
    # Step 3: Collect posts (for non-private users)
    public_users = [p["username"] for p in processed_profiles if not p.get("is_private")]
    print(f"\nCollecting posts for {len(public_users)} public users...")
    posts = collect_user_posts(public_users)
    
    processed_posts = []
    for post in posts:
        processed_posts.append({
            "username": post.get("username", ""),
            "post_date": post.get("timestamp", ""),
            "caption": post.get("caption", ""),
            "like_count": post.get("likesCount", 0),
            "comment_count": post.get("commentsCount", 0),
            "media_type": post.get("type", "Image"),
            "hashtags": post.get("hashtags", [])
        })
    
    with open(RAW_DIR / "posts.json", "w", encoding="utf-8") as f:
        json.dump(processed_posts, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(processed_posts)} posts")
    
    print("\n" + "=" * 60)
    print("Data collection complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
