"""Quick diagnostic to verify data loading"""
import pandas as pd
import os

RANKING_PATH = "data/processed/ranking.csv"
POSTS_PATH = "data/processed/posts_clean.csv"

def diagnose():
    print("=" * 50)
    print("DATA LOADING DIAGNOSTIC")
    print("=" * 50)
    
    # Load rankings
    print("\n[1] Ranking Data:")
    ranking = pd.read_csv(RANKING_PATH)
    print(f"  Rows: {len(ranking)}")
    print(f"  Columns: {list(ranking.columns)}")
    print(f"  Sample usernames: {ranking['username'].head(5).tolist()}")
    
    # Load posts
    print("\n[2] Posts Data:")
    posts = pd.read_csv(POSTS_PATH)
    print(f"  Rows: {len(posts)}")
    print(f"  Columns: {list(posts.columns)}")
    
    # Check column names
    print("\n[3] Column Check:")
    print(f"  'like_count' in posts: {'like_count' in posts.columns}")
    print(f"  'comment_count' in posts: {'comment_count' in posts.columns}")
    print(f"  'username' in posts: {'username' in posts.columns}")
    
    # Username matching
    print("\n[4] Username Matching:")
    ranking_users = set(ranking['username'].dropna().unique())
    posts_users = set(posts['username'].dropna().unique())
    
    matched = ranking_users & posts_users
    unmatched_ranking = ranking_users - posts_users
    
    print(f"  Ranking users: {len(ranking_users)}")
    print(f"  Posts users: {len(posts_users)}")
    print(f"  Matched: {len(matched)}")
    print(f"  Unmatched (in ranking but not in posts): {len(unmatched_ranking)}")
    
    if len(unmatched_ranking) > 0:
        print(f"  First 10 unmatched: {list(unmatched_ranking)[:10]}")
    
    # Sample data check
    print("\n[5] Sample Posts Check:")
    sample_user = list(matched)[0] if matched else None
    if sample_user:
        user_posts = posts[posts['username'] == sample_user]
        print(f"  User: {sample_user}")
        print(f"  Post count: {len(user_posts)}")
        if 'like_count' in posts.columns:
            print(f"  Avg likes: {user_posts['like_count'].mean():.1f}")
        if 'comment_count' in posts.columns:
            print(f"  Avg comments: {user_posts['comment_count'].mean():.1f}")

if __name__ == "__main__":
    diagnose()
