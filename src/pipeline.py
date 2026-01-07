"""
pipeline.py - End-to-end pipeline execution
"""
import sys
from pathlib import Path

# Add src to path for module imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.io_load import load_or_generate_data, PROCESSED_DIR, ensure_dirs
from src.cleaning import clean_participants, clean_posts, clean_comments
from src.features import compute_features
from src.scoring import apply_scores, apply_hard_filters, create_rankings


def run_pipeline():
    """
    Execute the full pipeline:
    1. Load or generate data
    2. Clean data
    3. Compute features
    4. Apply scoring
    5. Generate outputs
    """
    print("=" * 60)
    print("관계형 영향력 기반 러너 20명 선정 파이프라인")
    print("=" * 60)
    
    ensure_dirs()
    
    # Step 1: Load data
    print("\n[1/5] Loading data...")
    comments, profiles, posts = load_or_generate_data()
    
    # Step 2: Clean data
    print("\n[2/5] Cleaning data...")
    participants_df = clean_participants(profiles, posts)
    posts_df = clean_posts(posts)
    comments_df = clean_comments(comments)
    
    print(f"  - Participants: {len(participants_df)}")
    print(f"  - Posts: {len(posts_df)}")
    print(f"  - Comments: {len(comments_df)}")
    
    # Save cleaned data
    participants_df.to_csv(PROCESSED_DIR / "participants_clean.csv", index=False, encoding="utf-8-sig")
    posts_df.to_csv(PROCESSED_DIR / "posts_clean.csv", index=False, encoding="utf-8-sig")
    comments_df.to_csv(PROCESSED_DIR / "comments_clean.csv", index=False, encoding="utf-8-sig")
    
    # Step 3: Compute features
    print("\n[3/5] Computing features...")
    features_df = compute_features(participants_df, posts_df)
    features_df.to_csv(PROCESSED_DIR / "features.csv", index=False, encoding="utf-8-sig")
    print(f"  - Features computed for {len(features_df)} participants")
    
    # Step 4: Apply scoring
    print("\n[4/5] Applying scoring rules...")
    scored_df = apply_scores(participants_df, features_df)
    main_pool, excluded_pool = apply_hard_filters(scored_df)
    
    print(f"  - Main pool: {len(main_pool)}")
    print(f"  - Excluded (private/inactive): {len(excluded_pool)}")
    
    # Step 5: Create rankings
    print("\n[5/5] Creating rankings...")
    ranking, shortlist, winners_draft = create_rankings(main_pool, excluded_pool)
    
    ranking.to_csv(PROCESSED_DIR / "ranking.csv", index=False, encoding="utf-8-sig")
    shortlist.to_csv(PROCESSED_DIR / "shortlist.csv", index=False, encoding="utf-8-sig")
    winners_draft.to_csv(PROCESSED_DIR / "winners_draft.csv", index=False, encoding="utf-8-sig")
    
    # Report
    print("\n" + "=" * 60)
    print("파이프라인 완료!")
    print("=" * 60)
    
    print("\n[생성된 파일]")
    for f in ["participants_clean.csv", "posts_clean.csv", "comments_clean.csv",
              "features.csv", "ranking.csv", "shortlist.csv", "winners_draft.csv"]:
        filepath = PROCESSED_DIR / f
        if filepath.exists():
            print(f"  ✓ {f}")
        else:
            print(f"  ✗ {f} (MISSING)")
    
    # Top 10 preview
    print("\n[Ranking 상위 10명]")
    if len(ranking) > 0:
        preview_cols = ["rank", "username", "final_score", "relationship_score", 
                       "reliability_score", "runnerfit_score", "risk_flag"]
        available = [c for c in preview_cols if c in ranking.columns]
        print(ranking[available].head(10).to_string(index=False))
    else:
        print("  (No rankings available)")
    
    # Risk flag statistics
    print("\n[Risk Flag 통계]")
    if "risk_flag" in ranking.columns:
        flag_counts = {}
        for flags in ranking["risk_flag"]:
            if flags:
                for flag in flags.split("|"):
                    flag_counts[flag] = flag_counts.get(flag, 0) + 1
        
        if flag_counts:
            for flag, count in sorted(flag_counts.items()):
                print(f"  - {flag}: {count}명")
        else:
            print("  (No risk flags in main pool)")
    
    print(f"\n  - 제외된 참여자 (비공개/비활동): {len(excluded_pool)}명")
    
    return ranking, shortlist, winners_draft


if __name__ == "__main__":
    run_pipeline()
