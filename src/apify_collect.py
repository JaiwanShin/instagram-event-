"""
apify_collect.py - Collect Instagram data from event posts using Apify
"""
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any

# Apify API configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
BASE_URL = "https://api.apify.com/v2"

# Target Instagram posts (shortcodes)
TARGET_POSTS = [
    "DSuGGGvDFB7",
    "DSuGISfjPUk",
    "DSlsKZGE9KS"
]

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def run_apify_actor(actor_id: str, input_data: dict, wait: bool = True) -> List[Dict]:
    """
    Run an Apify actor and return results.
    """
    url = f"{BASE_URL}/acts/{actor_id}/runs"
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    
    print(f"[Apify] Starting actor: {actor_id}")
    
    response = requests.post(
        url,
        headers=headers,
        json=input_data,
        params={"waitForFinish": 300} if wait else {}
    )
    
    if response.status_code != 201:
        print(f"[Apify] Error starting actor: {response.status_code}")
        print(response.text)
        return []
    
    run_data = response.json()["data"]
    run_id = run_data["id"]
    print(f"[Apify] Run started: {run_id}")
    
    # Wait for completion if not already done
    if wait:
        status = run_data.get("status")
        while status not in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
            time.sleep(5)
            status_url = f"{BASE_URL}/actor-runs/{run_id}"
            status_resp = requests.get(status_url, headers=headers)
            if status_resp.status_code == 200:
                status = status_resp.json()["data"]["status"]
                print(f"[Apify] Status: {status}")
    
    # Get results
    dataset_id = run_data.get("defaultDatasetId")
    if not dataset_id:
        print("[Apify] No dataset found")
        return []
    
    items_url = f"{BASE_URL}/datasets/{dataset_id}/items"
    items_resp = requests.get(items_url, headers=headers)
    
    if items_resp.status_code == 200:
        items = items_resp.json()
        print(f"[Apify] Retrieved {len(items)} items")
        return items
    
    return []


def collect_post_comments(shortcode: str) -> List[Dict]:
    """
    Collect comments from a single Instagram post.
    """
    # Using apify/instagram-comment-scraper
    actor_id = "apify~instagram-comment-scraper"
    
    input_data = {
        "directUrls": [f"https://www.instagram.com/p/{shortcode}/"],
        "resultsLimit": 500,  # Get all comments
    }
    
    return run_apify_actor(actor_id, input_data)


def collect_user_profile(username: str) -> Dict:
    """
    Collect profile data for a single user.
    """
    # Using apify/instagram-profile-scraper
    actor_id = "apify~instagram-profile-scraper"
    
    input_data = {
        "usernames": [username],
    }
    
    results = run_apify_actor(actor_id, input_data)
    return results[0] if results else {}


def collect_user_posts(username: str, limit: int = 12) -> List[Dict]:
    """
    Collect recent posts from a user.
    """
    # Using apify/instagram-post-scraper
    actor_id = "apify~instagram-post-scraper"
    
    input_data = {
        "username": [username],
        "resultsLimit": limit,
    }
    
    return run_apify_actor(actor_id, input_data)


def collect_all_data():
    """
    Main collection function: collect comments, profiles, and posts.
    """
    ensure_dirs()
    
    all_comments = []
    unique_usernames = set()
    
    # Step 1: Collect comments from all target posts
    print("\n" + "=" * 60)
    print("Step 1: Collecting comments from event posts")
    print("=" * 60)
    
    for shortcode in TARGET_POSTS:
        print(f"\n[Collecting] Post: {shortcode}")
        comments = collect_post_comments(shortcode)
        
        for comment in comments:
            # Normalize comment data
            username = comment.get("ownerUsername") or comment.get("username")
            if username:
                unique_usernames.add(username)
                all_comments.append({
                    "username": username,
                    "comment_text": comment.get("text", ""),
                    "tagged_users_count": len(comment.get("mentions", [])),
                    "post_shortcode": shortcode
                })
        
        print(f"  - Collected {len(comments)} comments")
        time.sleep(2)  # Rate limiting
    
    # Deduplicate comments by username (keep first)
    seen_users = set()
    deduped_comments = []
    for c in all_comments:
        if c["username"] not in seen_users:
            seen_users.add(c["username"])
            deduped_comments.append(c)
    
    print(f"\nTotal unique participants: {len(unique_usernames)}")
    
    # Save comments
    with open(RAW_DIR / "comments.json", "w", encoding="utf-8") as f:
        json.dump(deduped_comments, f, ensure_ascii=False, indent=2)
    print(f"Saved comments to {RAW_DIR / 'comments.json'}")
    
    # Step 2: Collect profiles for all unique users
    print("\n" + "=" * 60)
    print("Step 2: Collecting user profiles")
    print("=" * 60)
    
    all_profiles = []
    for username in list(unique_usernames):
        print(f"[Profile] {username}")
        profile = collect_user_profile(username)
        if profile:
            all_profiles.append({
                "username": profile.get("username", username),
                "followers": profile.get("followersCount", 0),
                "following": profile.get("followsCount", 0),
                "is_private": profile.get("isPrivate", False),
                "post_count": profile.get("postsCount", 0),
                "bio": profile.get("biography", "")
            })
        time.sleep(1)
    
    with open(RAW_DIR / "profiles.json", "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, ensure_ascii=False, indent=2)
    print(f"Saved profiles to {RAW_DIR / 'profiles.json'}")
    
    # Step 3: Collect recent posts for each user
    print("\n" + "=" * 60)
    print("Step 3: Collecting user posts")
    print("=" * 60)
    
    all_posts = []
    for username in list(unique_usernames):
        # Skip private users
        profile = next((p for p in all_profiles if p["username"] == username), None)
        if profile and profile.get("is_private"):
            print(f"[Skip] {username} (private)")
            continue
        
        print(f"[Posts] {username}")
        posts = collect_user_posts(username, limit=12)
        
        for post in posts:
            all_posts.append({
                "username": username,
                "post_date": post.get("timestamp"),
                "caption": post.get("caption", ""),
                "like_count": post.get("likesCount", 0),
                "comment_count": post.get("commentsCount", 0),
                "media_type": post.get("type", "Image"),
                "hashtags": post.get("hashtags", [])
            })
        
        time.sleep(1)
    
    with open(RAW_DIR / "posts.json", "w", encoding="utf-8") as f:
        json.dump(all_posts, f, ensure_ascii=False, indent=2)
    print(f"Saved posts to {RAW_DIR / 'posts.json'}")
    
    print("\n" + "=" * 60)
    print("Data collection complete!")
    print(f"  - Comments: {len(deduped_comments)}")
    print(f"  - Profiles: {len(all_profiles)}")
    print(f"  - Posts: {len(all_posts)}")
    print("=" * 60)


if __name__ == "__main__":
    collect_all_data()
