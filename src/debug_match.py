import pandas as pd
import os

RANKING_PATH = "data/processed/ranking.csv"
POSTS_PATH = "data/processed/posts_clean.csv"

def debug_data():
    print("Loading data...")
    if not os.path.exists(POSTS_PATH):
        print("Posts file not found.")
        return

    try:
        posts = pd.read_csv(POSTS_PATH)
        ranking = pd.read_csv(RANKING_PATH)
        
        print(f"Posts shape: {posts.shape}")
        print(f"Ranking shape: {ranking.shape}")
        
        target_user = "kihwan.kim0505"
        
        # Check ranking
        if target_user in ranking["username"].values:
            print(f"'{target_user}' FOUND in Ranking.")
        else:
            print(f"'{target_user}' NOT found in Ranking.")
            # Search partial
            matches = [u for u in ranking["username"].dropna() if target_user in str(u)]
            print(f"Partial matches in Ranking: {matches}")

        # Check posts
        if target_user in posts["username"].values:
            print(f"'{target_user}' FOUND in Posts.")
            
            # Check metrics
            user_posts = posts[posts["username"] == target_user]
            print(f"Number of posts found: {len(user_posts)}")
            print(user_posts[["post_date", "like_count", "comment_count"]].head())
        else:
            print(f"'{target_user}' NOT found in Posts.")
            # Search partial
            matches = [u for u in posts["username"].dropna() if target_user in str(u)]
            print(f"Partial matches in Posts: {matches}")
            
            # Check for whitespace issues
            stripped_matches = [u for u in posts["username"].dropna() if target_user in str(u).strip()]
            if stripped_matches:
                 print(f"Found if stripped: {stripped_matches}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_data()
