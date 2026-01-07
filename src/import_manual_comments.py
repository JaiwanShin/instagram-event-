"""
import_manual_comments.py - Import user-provided comments CSV
"""
import pandas as pd
import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw"
COMMENTS_FILE = DATA_DIR / "comments.json"

def import_csv(csv_path: str):
    print(f"Importing comments from {csv_path}...")
    
    if not os.path.exists(csv_path):
        print(f"Error: File not found: {csv_path}")
        return
        
    try:
        # Try reading with header
        df = pd.read_csv(csv_path)
        
        # Check columns
        if "username" not in df.columns:
            # Maybe headerless?
            print("Warning: 'username' column not found. Assuming headerless: col 0=username, col 1=comment")
            df = pd.read_csv(csv_path, header=None, names=["username", "comment_text"])
            
        if "comment_text" not in df.columns and "comment" in df.columns:
            df = df.rename(columns={"comment": "comment_text"})
            
        # Clean
        df["username"] = df["username"].astype(str).str.strip()
        df["comment_text"] = df["comment_text"].fillna("").astype(str)
        
        # Convert to JSON format
        comments_data = []
        for _, row in df.iterrows():
            comments_data.append({
                "username": row["username"],
                "comment_text": row["comment_text"],
                "tagged_users_count": 0,
                "post_shortcode": "manual_import"
            })
            
        # Save
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(COMMENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(comments_data, f, ensure_ascii=False, indent=2)
            
        print(f"Successfully imported {len(comments_data)} comments to {COMMENTS_FILE}")
        print("Now you should run: python src/merge_and_fetch_missing.py")
        
    except Exception as e:
        print(f"Import failed: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        import_csv(sys.argv[1])
    else:
        print("Usage: python src/import_manual_comments.py <path_to_csv>")
