"""
merge_and_fetch_missing.py - Consolidate data and fetch missing profiles/posts
"""
import json
import time
import requests
from pathlib import Path

APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
BASE_URL = "https://api.apify.com/v2"

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

def load_json(filename):
    path = DATA_DIR / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_json(data, filename):
    with open(DATA_DIR / filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def collect_profiles(usernames):
    """Collect user profiles."""
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    actor_id = "apify~instagram-profile-scraper"
    
    all_profiles = []
    
    # Batch usernames (max 50)
    for i in range(0, len(usernames), 50):
        batch = usernames[i:i+50]
        print(f"Fetching profiles for {len(batch)} users...")
        
        input_data = {"usernames": batch}
        
        resp = requests.post(
            f"{BASE_URL}/acts/{actor_id}/runs",
            headers=headers,
            json=input_data,
            params={"waitForFinish": 300}
        )
        
        if resp.status_code == 201:
            run_data = resp.json()["data"]
            dataset_id = run_data["defaultDatasetId"]
            
            items_resp = requests.get(
                f"{BASE_URL}/datasets/{dataset_id}/items",
                headers=headers
            )
            if items_resp.status_code == 200:
                all_profiles.extend(items_resp.json())
                
    return all_profiles

def collect_user_posts(usernames, existing_private_users=set()):
    """Collect posts for users."""
    headers = {"Authorization": f"Bearer {APIFY_TOKEN}"}
    actor_id = "apify~instagram-post-scraper"
    
    all_posts = []
    
    for username in usernames:
        if username in existing_private_users:
            print(f"Skipping private user: {username}")
            continue
            
        print(f"Fetching posts for {username}")
        input_data = {
            "username": [username],
            "resultsLimit": 5,
        }
        
        resp = requests.post(
            f"{BASE_URL}/acts/{actor_id}/runs",
            headers=headers,
            json=input_data,
            params={"waitForFinish": 120}
        )
        
        if resp.status_code == 201:
            run_data = resp.json()["data"]
            dataset_id = run_data["defaultDatasetId"]
            
            items_resp = requests.get(
                f"{BASE_URL}/datasets/{dataset_id}/items",
                headers=headers
            )
            if items_resp.status_code == 200:
                posts = items_resp.json()
                for p in posts:
                    p["username"] = username
                    all_posts.append(p)
        time.sleep(1)
            
    return all_posts

def main():
    print("="*60)
    print("Merging and Fetching Missing Data")
    print("="*60)
    
    # 1. Load Data
    comments_v1 = load_json("comments.json")
    comments_v2 = load_json("comments_v2.json")
    profiles = load_json("profiles.json")
    posts = load_json("posts.json")
    
    print(f"Loaded: Comments V1({len(comments_v1)}), V2({len(comments_v2)})")
    print(f"Loaded: Profiles({len(profiles)}), Posts({len(posts)})")
    
    # 2. Consolidate Comments (Prefer V2, fallback to V1)
    all_comments = {c["username"]: c for c in comments_v1}
    # Update with V2 which should be more complete
    for c in comments_v2:
        all_comments[c["username"]] = c
        
    final_comments = list(all_comments.values())
    save_json(final_comments, "comments.json")
    print(f"Consolidated Comments: {len(final_comments)}")
    
    # 3. Identify Missing Profiles
    all_users = set(c["username"] for c in final_comments)
    existing_profiles = set(p["username"] for p in profiles)
    missing_users = list(all_users - existing_profiles)
    
    print(f"Missing Profiles: {len(missing_users)}")
    
    if missing_users:
        new_profiles_raw = collect_profiles(missing_users)
        
        # Process and normalize
        for p in new_profiles_raw:
            profiles.append({
                "username": p.get("username", ""),
                "followers": p.get("followersCount", 0),
                "following": p.get("followsCount", 0),
                "is_private": p.get("isPrivate", False),
                "post_count": p.get("postsCount", 0),
                "bio": p.get("biography", "")
            })
        
        save_json(profiles, "profiles.json")
        print(f"Updated Profiles: {len(profiles)} (Fetched {len(new_profiles_raw)})")
    
    # 4. Identify Missing Posts
    # We need posts for ALL users (except private ones)
    # Check coverage
    users_with_posts = set(p["username"] for p in posts)
    
    # Re-evaluate who needs posts (newly fetched profiles + any previous gaps)
    # But only for users we actually have profiles for (to check private status)
    profile_map = {p["username"]: p for p in profiles}
    
    users_needing_posts = []
    for u in all_users:
        if u not in users_with_posts:
            # Check if private
            user_prof = profile_map.get(u)
            if user_prof and not user_prof.get("is_private"):
                users_needing_posts.append(u)
    
    print(f"Users needing posts: {len(users_needing_posts)}")
    
    if users_needing_posts:
        print(f"Fetching posts for {len(users_needing_posts)} users...")
        new_posts_raw = collect_user_posts(users_needing_posts)
        
        # Process
        for p in new_posts_raw:
            posts.append({
                "username": p.get("username", ""),
                "post_date": p.get("timestamp", ""),
                "caption": p.get("caption", ""),
                "like_count": p.get("likesCount", 0),
                "comment_count": p.get("commentsCount", 0),
                "media_type": p.get("type", "Image"),
                "hashtags": p.get("hashtags", []),
                "post_url": p.get("url", f"https://www.instagram.com/p/{p.get('shortCode', '')}/"),
                "shortcode": p.get("shortCode", "")
            })
            
        save_json(posts, "posts.json")
        print(f"Updated Posts: {len(posts)} (Fetched {len(new_posts_raw)})")
    
    print("\nData Sync Complete!")

if __name__ == "__main__":
    main()
