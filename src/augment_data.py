"""
augment_data.py - Augment collected data with synthetic samples to reach target size
"""
import json
import random
from pathlib import Path
from src.io_load import generate_sample_data, load_json, save_json

TARGET_SIZE = 100

def augment_data():
    print("=" * 60)
    print("데이터 증강 (Data Augmentation)")
    print("=" * 60)
    
    # Load existing real data
    real_comments = load_json("comments.json")
    real_profiles = load_json("profiles.json")
    real_posts = load_json("posts.json")
    
    current_count = len(set(c["username"] for c in real_comments))
    print(f"현재 수집된 실제 참여자 수: {current_count}명")
    
    if current_count >= TARGET_SIZE:
        print("목표 인원을 충족하여 증강하지 않습니다.")
        return

    missing_count = TARGET_SIZE - current_count
    print(f"목표({TARGET_SIZE}명) 달성을 위해 {missing_count}명의 샘플 데이터를 생성합니다.")
    
    # Generate sample data
    sample_comments, sample_profiles, sample_posts = generate_sample_data(missing_count)
    
    # Add identifier to sample users to distinguish them later
    for p in sample_profiles:
        p["is_sample"] = True
        p["bio"] = "[Sample] " + p["bio"]
    
    # Merge
    final_comments = real_comments + sample_comments
    final_profiles = real_profiles + sample_profiles
    final_posts = real_posts + sample_posts
    
    # Save merged data
    save_json(final_comments, "comments.json")
    save_json(final_profiles, "profiles.json")
    save_json(final_posts, "posts.json")
    
    print(f"\n[완료] 총 {len(final_profiles)}명의 데이터가 준비되었습니다.")
    print(f"  - 실제 데이터: {current_count}명")
    print(f"  - 샘플 데이터: {missing_count}명")

if __name__ == "__main__":
    augment_data()
