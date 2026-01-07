"""
debug_pipeline.py - Inspect intermediate dataframes
"""
import pandas as pd
from src.io_load import load_or_generate_data
from src.cleaning import clean_participants, clean_posts
from datetime import datetime, timedelta

def debug():
    print("DEBUG: Loading data...")
    comments, profiles, posts = load_or_generate_data()
    
    print(f"DEBUG: Profiles: {len(profiles)}")
    print(f"DEBUG: Posts: {len(posts)}")
    
    # Check Sample Profile
    p0 = profiles[0]
    print(f"DEBUG: Profile[0]: {p0['username']}")
    
    # Check Sample Post for that user
    user_posts = [p for p in posts if p.get("username") == p0['username']]
    print(f"DEBUG: Profile[0] has {len(user_posts)} posts in raw list")
    if user_posts:
        print(f"DEBUG: Post[0] date: {user_posts[0].get('post_date')}")

    # Run Clean
    print("\nDEBUG: Running Clean...")
    participants_df = clean_participants(profiles, posts)
    
    # Inspect Result for that user
    row = participants_df[participants_df["username"] == p0['username']]
    if not row.empty:
        print("DEBUG: Cleaned Participant Row:")
        print(row.iloc[0][["username", "posts_90d", "last_post_days", "is_private"]])
    else:
        print("DEBUG: Participant not found in cleaned df!")
        
    # Check date logic
    now = datetime.now()
    cutoff = now - timedelta(days=90)
    print(f"\nDEBUG: Current Time: {now}")
    print(f"DEBUG: Cutoff Time: {cutoff}")
    
    # Check if that post should have counted
    if user_posts:
        # manual parse
        d_str = user_posts[0].get('post_date')
        if d_str:
            try:
                dt = pd.to_datetime(d_str)
                print(f"DEBUG: Parsed Date: {dt}")
                print(f"DEBUG: Is >= Cutoff? {dt >= cutoff}")
            except Exception as e:
                print(f"DEBUG: Date parse error: {e}")

if __name__ == "__main__":
    debug()
