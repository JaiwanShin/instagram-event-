"""
check_status.py - Check counts of collected data
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"

def check():
    if not RAW_DIR.exists():
        print("No data directory.")
        return

    comments_file = RAW_DIR / "comments.json"
    profiles_file = RAW_DIR / "profiles.json"
    posts_file = RAW_DIR / "posts.json"
    
    c_count = 0
    p_count = 0
    po_count = 0
    
    if comments_file.exists():
        with open(comments_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            c_count = len(data)
            unique_c = len(set(c.get("username") for c in data))
            print(f"Comments: {c_count} (Unique Users: {unique_c})")
            
    if profiles_file.exists():
        with open(profiles_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            p_count = len(data)
            print(f"Profiles: {p_count}")
            
    if posts_file.exists():
        with open(posts_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            po_count = len(data)
            print(f"Posts: {po_count}")

if __name__ == "__main__":
    check()
