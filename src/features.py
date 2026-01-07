"""
features.py - Feature engineering for relationship-based runner selection
"""
import pandas as pd
import numpy as np
from typing import Tuple

# Running keywords for RunnerFit score
RUNNING_KEYWORDS = [
    "러닝", "런닝", "러너", "러닝크루", "마라톤", "하프", 
    "10k", "5k", "런린이", "트레일러닝"
]


def compute_features(
    participants_df: pd.DataFrame,
    posts_df: pd.DataFrame,
    n_recent: int = 12
) -> pd.DataFrame:
    """
    Compute relationship-focused features for each participant.
    
    Features:
    - avg_comments_12: Average comments on last N posts
    - avg_likes_12: Average likes on last N posts  
    - comment_like_ratio: avg_comments / max(avg_likes, 1)
    - low_comment_post_rate: Ratio of posts with 0-1 comments
    - community_signal: log1p(avg_comments) + 0.5*comment_like_ratio - low_comment_post_rate
    - running_hashtag_rate: Ratio of posts with running keywords
    """
    features = []
    
    for _, participant in participants_df.iterrows():
        username = participant["username"]
        user_posts = posts_df[posts_df["username"] == username].copy()
        
        # Sort by date and take N most recent
        if not user_posts.empty and "post_date" in user_posts.columns:
            user_posts = user_posts.sort_values("post_date", ascending=False).head(n_recent)
        
        n_posts = len(user_posts)
        
        if n_posts == 0:
            # No posts available
            features.append({
                "username": username,
                "avg_comments_12": 0,
                "avg_likes_12": 0,
                "comment_like_ratio": 0,
                "low_comment_post_rate": 1.0,
                "community_signal": 0,
                "running_hashtag_rate": 0
            })
            continue
        
        # Engagement metrics - filter out invalid like_count (-1 means data not available)
        valid_likes = user_posts[user_posts["like_count"] >= 0]["like_count"]
        avg_comments = user_posts["comment_count"].mean()
        avg_likes = valid_likes.mean() if len(valid_likes) > 0 else 0
        comment_like_ratio = avg_comments / max(avg_likes, 1) if avg_likes > 0 else 0
        
        # Low comment post rate (posts with <=3 comments, excluding invalid data)
        valid_comment_posts = user_posts[user_posts["comment_count"] >= 0]
        if len(valid_comment_posts) > 0:
            low_comment_posts = (valid_comment_posts["comment_count"] <= 3).sum()
            low_comment_post_rate = low_comment_posts / len(valid_comment_posts)
        else:
            low_comment_post_rate = 1.0
        
        # Community signal (higher is better community engagement)
        community_signal = np.log1p(avg_comments) + 0.5 * comment_like_ratio - low_comment_post_rate
        
        # Running hashtag rate
        running_posts = 0
        for _, post in user_posts.iterrows():
            caption = str(post.get("caption", "")).lower()
            hashtags = post.get("hashtags", [])
            hashtag_text = " ".join([str(h).lower() for h in hashtags]) if isinstance(hashtags, list) else ""
            combined_text = caption + " " + hashtag_text
            
            if any(keyword.lower() in combined_text for keyword in RUNNING_KEYWORDS):
                running_posts += 1
        
        running_hashtag_rate = running_posts / n_posts
        
        features.append({
            "username": username,
            "avg_comments_12": round(avg_comments, 2),
            "avg_likes_12": round(avg_likes, 2),
            "comment_like_ratio": round(comment_like_ratio, 4),
            "low_comment_post_rate": round(low_comment_post_rate, 4),
            "community_signal": round(community_signal, 4),
            "running_hashtag_rate": round(running_hashtag_rate, 4)
        })
    
    return pd.DataFrame(features)


if __name__ == "__main__":
    from .io_load import load_or_generate_data
    from .cleaning import clean_participants, clean_posts
    
    comments, profiles, posts = load_or_generate_data()
    participants_df = clean_participants(profiles, posts)
    posts_df = clean_posts(posts)
    
    features_df = compute_features(participants_df, posts_df)
    print(features_df.head(10))
