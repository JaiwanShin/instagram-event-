"""
cleaning.py - Data preprocessing and cleaning
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .io_load import normalize_record


# -----------------------------------------------------------------------------
# Cleaning Functions
# -----------------------------------------------------------------------------
def clean_participants(profiles: list, posts: list) -> pd.DataFrame:
    """
    Clean and enrich participant profiles with activity metrics.
    
    Output columns:
    - username, is_private, followers, following, post_count, bio
    - last_post_date, last_post_days, posts_90d
    """
    # Normalize profiles
    profile_keys = ["username", "followers", "following", "is_private", "post_count", "bio"]
    df = pd.DataFrame([normalize_record(p, profile_keys) for p in profiles])
    
    if df.empty:
        return pd.DataFrame(columns=profile_keys + ["last_post_date", "last_post_days", "posts_90d"])
    
    # Handle missing values
    df["is_private"] = df["is_private"].fillna(False).astype(bool)
    df["followers"] = pd.to_numeric(df["followers"], errors="coerce").fillna(0).astype(int)
    df["following"] = pd.to_numeric(df["following"], errors="coerce").fillna(0).astype(int)
    df["post_count"] = pd.to_numeric(df["post_count"], errors="coerce").fillna(0).astype(int)
    df["bio"] = df["bio"].fillna("")
    
    # Calculate activity metrics from posts
    # Use UTC for consistency as Apify returns UTC dates
    now = datetime.now().astimezone()
    cutoff_90d = now - timedelta(days=90)
    
    posts_df = pd.DataFrame(posts) if posts else pd.DataFrame()
    
    if not posts_df.empty:
        # Normalize post dates
        posts_df["username"] = posts_df.apply(
            lambda r: normalize_record(r.to_dict(), ["username"])["username"], axis=1
        )
        posts_df["post_date"] = posts_df.apply(
            lambda r: normalize_record(r.to_dict(), ["post_date"])["post_date"], axis=1
        )
        posts_df["post_date"] = pd.to_datetime(posts_df["post_date"], errors="coerce", utc=True)
        
        # Last post date per user
        last_post = posts_df.groupby("username")["post_date"].max().reset_index()
        last_post.columns = ["username", "last_post_date"]
        
        # Posts in last 90 days per user
        posts_90d = posts_df[posts_df["post_date"] >= cutoff_90d].groupby("username").size().reset_index(name="posts_90d")
        
        # Merge with profiles
        df = df.merge(last_post, on="username", how="left")
        df = df.merge(posts_90d, on="username", how="left")
    else:
        df["last_post_date"] = pd.NaT
        df["posts_90d"] = 0
    
    # Calculate days since last post
    df["last_post_date"] = pd.to_datetime(df["last_post_date"], errors="coerce")
    df["last_post_days"] = (now - df["last_post_date"]).dt.days.fillna(999).astype(int)
    df["posts_90d"] = df["posts_90d"].fillna(0).astype(int)
    
    # Deduplicate by username
    df = df.drop_duplicates(subset=["username"], keep="first")
    
    return df


def clean_posts(posts: list) -> pd.DataFrame:
    """
    Clean posts data.
    
    Output columns:
    - username, post_date, caption, like_count, comment_count, media_type, hashtags, post_url
    """
    post_keys = ["username", "post_date", "caption", "like_count", "comment_count", "media_type", "hashtags", "post_url"]
    df = pd.DataFrame([normalize_record(p, post_keys) for p in posts])
    
    if df.empty:
        return pd.DataFrame(columns=post_keys)
    
    # Type conversions
    df["post_date"] = pd.to_datetime(df["post_date"], errors="coerce")
    df["like_count"] = pd.to_numeric(df["like_count"], errors="coerce").fillna(0).astype(int)
    df["comment_count"] = pd.to_numeric(df["comment_count"], errors="coerce").fillna(0).astype(int)
    df["caption"] = df["caption"].fillna("")
    df["post_url"] = df["post_url"].fillna("")
    df["media_type"] = df["media_type"].fillna("Unknown")
    df["hashtags"] = df["hashtags"].apply(lambda x: x if isinstance(x, list) else [])
    
    return df


def clean_comments(comments: list) -> pd.DataFrame:
    """
    Clean comments data.
    
    Output columns:
    - username, comment_text, comment_len, tagged_users_count
    """
    comment_keys = ["username", "comment_text", "tagged_users_count", "post_shortcode"]
    df = pd.DataFrame([normalize_record(c, comment_keys) for c in comments])
    
    if df.empty:
        return pd.DataFrame(columns=comment_keys + ["comment_len"])
    
    df["comment_text"] = df["comment_text"].fillna("")
    df["comment_len"] = df["comment_text"].str.len()
    df["tagged_users_count"] = pd.to_numeric(df["tagged_users_count"], errors="coerce").fillna(0).astype(int)
    
    # Deduplicate comments by username (keep first comment per user)
    df = df.drop_duplicates(subset=["username"], keep="first")
    
    return df


if __name__ == "__main__":
    from .io_load import load_or_generate_data
    comments, profiles, posts = load_or_generate_data()
    
    participants_df = clean_participants(profiles, posts)
    posts_df = clean_posts(posts)
    comments_df = clean_comments(comments)
    
    print(f"Participants: {len(participants_df)}")
    print(f"Posts: {len(posts_df)}")
    print(f"Comments: {len(comments_df)}")
