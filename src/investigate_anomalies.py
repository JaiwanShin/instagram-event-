"""Investigate data anomalies"""
import pandas as pd

RANKING_PATH = "data/processed/ranking.csv"
POSTS_PATH = "data/processed/posts_clean.csv"

def investigate():
    print("=" * 60)
    print("DATA ANOMALY INVESTIGATION")
    print("=" * 60)
    
    ranking = pd.read_csv(RANKING_PATH)
    posts = pd.read_csv(POSTS_PATH)
    
    # 1. Check for negative likes in posts
    print("\n[1] Negative Likes in Posts:")
    if 'like_count' in posts.columns:
        neg_likes = posts[posts['like_count'] < 0]
        print(f"  Posts with negative likes: {len(neg_likes)}")
        if len(neg_likes) > 0:
            print(neg_likes[['username', 'like_count']].head(10))
    
    # 2. Check avg_likes_12 in ranking
    print("\n[2] Avg Likes in Ranking:")
    if 'avg_likes_12' in ranking.columns:
        print(f"  Min: {ranking['avg_likes_12'].min()}")
        print(f"  Max: {ranking['avg_likes_12'].max()}")
        neg_avg = ranking[ranking['avg_likes_12'] < 0]
        print(f"  Users with negative avg_likes: {len(neg_avg)}")
        if len(neg_avg) > 0:
            print(neg_avg[['username', 'avg_likes_12']].head(10))
    else:
        print("  'avg_likes_12' column NOT FOUND in ranking.csv")
        print(f"  Available columns: {list(ranking.columns)}")
    
    # 3. Check low_comment_post_rate
    print("\n[3] Low Comment Post Rate:")
    if 'low_comment_post_rate' in ranking.columns:
        zero_rate = ranking[ranking['low_comment_post_rate'] == 0]
        print(f"  Users with rate = 0: {len(zero_rate)} / {len(ranking)}")
        print(f"  Min: {ranking['low_comment_post_rate'].min()}")
        print(f"  Max: {ranking['low_comment_post_rate'].max()}")
    else:
        print("  'low_comment_post_rate' column NOT FOUND in ranking.csv")
    
    # 4. Check data sync - sample user
    print("\n[4] Data Sync Check (Sample User):")
    sample_user = ranking.iloc[0]['username']
    print(f"  User: {sample_user}")
    
    user_posts = posts[posts['username'] == sample_user]
    print(f"  Posts in posts_clean.csv: {len(user_posts)}")
    
    if len(user_posts) > 0 and 'like_count' in user_posts.columns:
        calc_avg_likes = user_posts['like_count'].head(12).mean()
        print(f"  Calculated avg_likes (recent 12): {calc_avg_likes:.1f}")
        
        if 'avg_likes_12' in ranking.columns:
            stored_avg = ranking[ranking['username'] == sample_user]['avg_likes_12'].values[0]
            print(f"  Stored in ranking.csv: {stored_avg}")
        
        if 'comment_count' in user_posts.columns:
            low_comment = len(user_posts.head(12)[user_posts.head(12)['comment_count'] <= 3])
            calc_rate = low_comment / min(12, len(user_posts))
            print(f"  Calculated low_comment_rate: {calc_rate:.2f}")

if __name__ == "__main__":
    investigate()
