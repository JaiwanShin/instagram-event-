"""
io_load.py - Data loading utilities and sample data generation
"""
import json
import random
import os
from datetime import datetime, timedelta
from pathlib import Path

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"


def ensure_dirs():
    """Ensure data directories exist."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------------------------------
# Flexible Key Mapping
# -----------------------------------------------------------------------------
KEY_ALIASES = {
    # comments.json
    "username": ["username", "ownerUsername", "user", "owner"],
    "comment_text": ["comment_text", "text", "body", "content"],
    "tagged_users_count": ["tagged_users_count", "mentions_count", "tagged_count"],
    "post_shortcode": ["post_shortcode", "shortcode", "postId"],
    # profiles.json
    "followers": ["followers", "followersCount", "follower_count"],
    "following": ["following", "followsCount", "following_count"],
    "is_private": ["is_private", "isPrivate", "private"],
    "post_count": ["post_count", "postsCount", "mediaCount"],
    "bio": ["bio", "biography", "description"],
    # posts.json
    "post_date": ["post_date", "timestamp", "taken_at", "date", "datetime"],
    "caption": ["caption", "text", "description"],
    "like_count": ["like_count", "likesCount", "likes"],
    "comment_count": ["comment_count", "commentsCount", "comments"],
    "media_type": ["media_type", "type", "mediaType"],
    "hashtags": ["hashtags", "tags", "hashTags"],
    "post_url": ["post_url", "url", "permalink"],
}


def map_key(record: dict, target_key: str):
    """Get value from record using flexible key mapping."""
    aliases = KEY_ALIASES.get(target_key, [target_key])
    for alias in aliases:
        if alias in record:
            return record[alias]
    return None


def normalize_record(record: dict, keys: list) -> dict:
    """Normalize a record by mapping keys to standard names."""
    return {key: map_key(record, key) for key in keys}


# -----------------------------------------------------------------------------
# JSON Loading
# -----------------------------------------------------------------------------
def load_json(filename: str):
    """Load JSON file from raw directory."""
    filepath = RAW_DIR / filename
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, list) else [data]


def save_json(data: list, filename: str):
    """Save data to JSON file in raw directory."""
    ensure_dirs()
    filepath = RAW_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[io_load] Saved {len(data)} records to {filepath}")


# -----------------------------------------------------------------------------
# Sample Data Generation (when Apify data not available)
# -----------------------------------------------------------------------------
RUNNING_KEYWORDS = ["러닝", "런닝", "러너", "러닝크루", "마라톤", "하프", "10k", "5k", "런린이", "트레일러닝"]
SAMPLE_BIOS = [
    "러닝을 사랑하는 🏃‍♂️ | 마라톤 완주 3회",
    "일상을 달리다 | 러닝크루 멤버",
    "Daily runner 🏃‍♀️ #런린이",
    "여행 좋아하는 사람",
    "커피와 책을 좋아해요 ☕📚",
    "맛집 탐방러 🍜",
    "10k 목표 달성 중!",
    "트레일러닝 입문자",
    "",
    "하프마라톤 도전 중",
]


def generate_sample_data(n_users: int = 50) -> tuple:
    """
    Generate sample data for testing when Apify data is not available.
    Creates diverse user profiles: runners, non-runners, inactive, private accounts.
    """
    random.seed(42)
    now = datetime.now()
    
    comments = []
    profiles = []
    posts = []
    
    post_shortcodes = ["DSuGGGvDFB7", "DSuGISfjPUk", "DSlsKZGE9KS"]
    
    for i in range(n_users):
        username = f"user_{i:03d}"
        
        # User type distribution
        is_runner = random.random() < 0.6  # 60% runners
        is_private = random.random() < 0.15  # 15% private
        is_active = random.random() < 0.85  # 85% active
        
        # Profile
        followers = random.randint(100, 5000) if is_runner else random.randint(50, 1000)
        following = random.randint(100, 800)
        post_count = random.randint(10, 200) if is_active else random.randint(1, 5)
        bio = random.choice([b for b in SAMPLE_BIOS if (RUNNING_KEYWORDS[0] in b.lower() or "러" in b) == is_runner] or SAMPLE_BIOS)
        
        profiles.append({
            "username": username,
            "followers": followers,
            "following": following,
            "is_private": is_private,
            "post_count": post_count,
            "bio": bio
        })
        
        # Comments (1-3 per user across event posts)
        n_comments = random.randint(1, 3)
        for _ in range(n_comments):
            post_code = random.choice(post_shortcodes)
            tagged = random.randint(0, 3)
            comment = f"@friend{random.randint(1,10)} 함께해요!" if tagged > 0 else "참여합니다!"
            comments.append({
                "username": username,
                "comment_text": comment,
                "tagged_users_count": tagged,
                "post_shortcode": post_code
            })
        
        # User's posts (0-20 recent posts)
        if is_private:
            continue  # Private users have no visible posts
            
        n_posts = random.randint(0, 20) if is_active else random.randint(0, 2)
        for j in range(n_posts):
            days_ago = random.randint(0, 120)
            post_date = (now - timedelta(days=days_ago)).isoformat()
            
            # Running content for runners
            if is_runner and random.random() < 0.7:
                caption = f"오늘도 {random.choice(RUNNING_KEYWORDS)} 완료! #{random.choice(RUNNING_KEYWORDS)}"
                hashtags = random.sample(RUNNING_KEYWORDS, k=min(3, len(RUNNING_KEYWORDS)))
            else:
                caption = "오늘의 일상 #daily"
                hashtags = ["daily", "일상", "instadaily"]
            
            # Engagement based on runner/community level
            if is_runner:
                like_count = random.randint(20, 300)
                comment_count = random.randint(0, 15)
            else:
                like_count = random.randint(5, 50)
                comment_count = random.randint(0, 3)
            
            posts.append({
                "username": username,
                "post_date": post_date,
                "caption": caption,
                "like_count": like_count,
                "comment_count": comment_count,
                "media_type": random.choice(["Image", "Video", "Carousel"]),
                "hashtags": hashtags
            })
    
    return comments, profiles, posts


def load_or_generate_data():
    """Load existing data or generate sample data if not available."""
    ensure_dirs()
    
    comments_file = RAW_DIR / "comments.json"
    profiles_file = RAW_DIR / "profiles.json"
    posts_file = RAW_DIR / "posts.json"
    
    # Check if any data exists
    if not comments_file.exists() or not profiles_file.exists() or not posts_file.exists():
        print("[io_load] Raw data not found. Generating sample data...")
        comments, profiles, posts = generate_sample_data(50)
        save_json(comments, "comments.json")
        save_json(profiles, "profiles.json")
        save_json(posts, "posts.json")
    
    # Load data
    comments = load_json("comments.json")
    profiles = load_json("profiles.json")
    posts = load_json("posts.json")
    
    print(f"[io_load] Loaded: {len(comments)} comments, {len(profiles)} profiles, {len(posts)} posts")
    
    return comments, profiles, posts


if __name__ == "__main__":
    load_or_generate_data()
