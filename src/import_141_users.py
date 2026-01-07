"""
import_141_users.py - Import 141+ users from CSV and setup complete pipeline
"""
import pandas as pd
import json
import shutil
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
BACKUP_DIR = DATA_DIR / "backup"
CSV_PATH = BASE_DIR / "username and comment.csv"

def backup_existing():
    """Backup existing raw data files"""
    if not BACKUP_DIR.exists():
        BACKUP_DIR.mkdir(parents=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for filename in ["comments.json", "profiles.json", "posts.json"]:
        src = DATA_DIR / filename
        if src.exists():
            dst = BACKUP_DIR / f"{filename.replace('.json', '')}_{timestamp}.json"
            shutil.copy(src, dst)
            print(f"Backed up: {filename} -> {dst.name}")

def import_comments():
    """Import comments from CSV"""
    print("=" * 60)
    print("Importing Manual Comments from CSV")
    print("=" * 60)
    
    # Backup first
    backup_existing()
    
    # Read CSV
    df = pd.read_csv(CSV_PATH)
    print(f"Loaded {len(df)} rows from CSV")
    
    # Check for required columns
    if "username" not in df.columns:
        print("Error: 'username' column not found!")
        return
    
    # Clean data
    df = df.dropna(subset=["username"])
    df["username"] = df["username"].astype(str).str.strip()
    df = df[df["username"] != ""]
    
    # Convert to comments.json format
    comments_data = []
    for _, row in df.iterrows():
        username = row["username"]
        # Get comment text (combined or single)
        comment_text = str(row.get("comment_combined", row.get("comment", "")))
        
        comments_data.append({
            "username": username,
            "comment_text": comment_text,
            "tagged_users_count": comment_text.count("@"),
            "post_shortcode": "manual_import"
        })
    
    # Remove duplicates by username
    seen = set()
    unique_comments = []
    for c in comments_data:
        if c["username"] not in seen:
            seen.add(c["username"])
            unique_comments.append(c)
    
    print(f"Unique users: {len(unique_comments)}")
    
    # Save
    with open(DATA_DIR / "comments.json", "w", encoding="utf-8") as f:
        json.dump(unique_comments, f, ensure_ascii=False, indent=2)
    print(f"Saved: comments.json ({len(unique_comments)} records)")
    
    # Clear profiles and posts to force re-fetch
    for filename in ["profiles.json", "posts.json"]:
        filepath = DATA_DIR / filename
        if filepath.exists():
            # Save empty list
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump([], f)
            print(f"Cleared: {filename}")
    
    print("\n" + "=" * 60)
    print("Import Complete!")
    print("=" * 60)
    print(f"\nNext Steps:")
    print("1. Run: python src/merge_and_fetch_missing.py")
    print("2. Run: python -m src.pipeline")
    
    return len(unique_comments)

if __name__ == "__main__":
    import_comments()
