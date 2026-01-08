"""
scoring.py - Tiered scoring system for runner selection
"""
import pandas as pd
import numpy as np
from typing import Tuple


# =============================================================================
# HARD-CODED SCORING RULES
# =============================================================================

def score_avg_comments(avg_comments: float) -> int:
    """
    A) avg_comments_12 -> Relationship 댓글 기반 점수 (30점 만점)
    
    평균 댓글 수에 따른 기본 점수:
    <0.5: 3점, 0.5~1: 6점, 1~2: 12점, 2~4: 21점, >=4: 30점
    """
    if avg_comments < 0.5:
        return 3
    elif avg_comments < 1:
        return 6
    elif avg_comments < 2:
        return 12
    elif avg_comments < 4:
        return 21
    else:
        return 30


def score_low_comment_penalty(low_comment_rate: float) -> int:
    """
    B) low_comment_post_rate penalty (added to Relationship)
    >=0.8: -15, 0.6~0.8: -10, 0.4~0.6: -5, <0.4: 0
    """
    if low_comment_rate >= 0.8:
        return -15
    elif low_comment_rate >= 0.6:
        return -10
    elif low_comment_rate >= 0.4:
        return -5
    else:
        return 0


def score_last_post_days(days: int) -> int:
    """
    C) last_post_days -> Reliability score
    <=7: 30, 8~14: 25, 15~30: 18, 31~60: 10, 61~90: 5, >90: 0
    """
    if days <= 7:
        return 30
    elif days <= 14:
        return 25
    elif days <= 30:
        return 18
    elif days <= 60:
        return 10
    elif days <= 90:
        return 5
    else:
        return 0


def score_posts_90d(posts_90d: int) -> int:
    """
    D) posts_90d score (added to Reliability base from last_post_days)
    0: 0, 1: 10, 2~3: 20, >=4: 30
    
    NOTE: Adjusted for fetch limit of 5.
    """
    if posts_90d == 0:
        return 0
    elif posts_90d <= 1:
        return 10
    elif posts_90d <= 3:
        return 20
    else:
        return 30


def score_is_private_penalty(is_private: bool) -> int:
    """
    E) is_private penalty for Reliability
    private: -10, public: 0
    """
    return -10 if is_private else 0


def score_running_hashtag(rate: float) -> int:
    """
    F) running_hashtag_rate -> RunnerFit score
    0: 0, (0~0.25]: 5, (0.25~0.5]: 10, (0.5~0.75]: 15, >0.75: 20
    """
    if rate == 0:
        return 0
    elif rate <= 0.25:
        return 5
    elif rate <= 0.5:
        return 10
    elif rate <= 0.75:
        return 15
    else:
        return 20


def score_engagement_rate(engagement_rate: float) -> int:
    """
    G) engagement_rate -> Engagement 효율성 점수 (20점 만점)
    
    [의미] 팔로워 대비 댓글 참여율
    - 팔로워가 적어도 참여율이 높으면 진정한 커뮤니티가 있다는 신호
    - 대규모 팔로워지만 참여가 적으면 낮은 점수
    
    [수식] engagement_rate = (평균 댓글 수 / 팔로워 수) × 100
    
    [구간 점수]
    >= 1.0%: 20점 (매우 높은 참여율 - 소규모 밀착 커뮤니티)
    0.5~1.0%: 15점 (높은 참여율)
    0.2~0.5%: 10점 (보통 참여율)
    0.1~0.2%: 5점 (낮은 참여율)
    < 0.1%: 0점 (매우 낮은 참여율 - 소통 부족)
    
    [예시]
    - 팔로워 1,000명, 평균 댓글 10개 → 1.0% → 20점
    - 팔로워 10,000명, 평균 댓글 10개 → 0.1% → 5점
    """
    if engagement_rate >= 1.0:
        return 20
    elif engagement_rate >= 0.5:
        return 15
    elif engagement_rate >= 0.2:
        return 10
    elif engagement_rate >= 0.1:
        return 5
    else:
        return 0


# =============================================================================
# Main Scoring Functions
# =============================================================================

def compute_relationship_score(row: pd.Series) -> int:
    """
    Relationship Score (관계성 점수, 0-50점)
    
    [의미] 팔로워와 얼마나 진정성 있게 소통하는가?
    - 댓글 많음 = 활발한 소통
    - 참여율 높음 = 효율적 소통 (팔로워 대비)
    
    [수식]
    = 댓글 기반 점수 (30점) + Engagement Rate 점수 (20점) + 페널티
    
    [예시]
    - 평균 댓글 5개 (30점) + 참여율 1% (20점) = 50점 (만점)
    - 평균 댓글 5개 (30점) + 참여율 0.05% (0점) = 30점
    """
    comment_score = score_avg_comments(row["avg_comments_12"])
    engagement_score = score_engagement_rate(row.get("engagement_rate", 0))
    penalty = score_low_comment_penalty(row["low_comment_post_rate"])
    return max(0, min(50, comment_score + engagement_score + penalty))


def compute_reliability_score(row: pd.Series) -> int:
    """
    Reliability Score (0-30)
    = (score_last_post_days + score_posts_90d) / 2 + is_private_penalty
    Clamped to [0, 30]
    
    Since C max=30 and D max=30, we average them to get base 0-30.
    """
    last_post_score = score_last_post_days(row["last_post_days"])
    posts_90d_score = score_posts_90d(row["posts_90d"])
    # Average the two components (both 0-30 max)
    base = (last_post_score + posts_90d_score) / 2
    penalty = score_is_private_penalty(row["is_private"])
    return max(0, min(30, int(base + penalty)))


def compute_runnerfit_score(row: pd.Series) -> int:
    """
    RunnerFit Score (0-20)
    = score_running_hashtag
    """
    return score_running_hashtag(row["running_hashtag_rate"])


def compute_final_score(
    relationship: int,
    reliability: int,
    runnerfit: int
) -> float:
    """
    Final Score = 0.50*Relationship + 0.30*Reliability + 0.20*RunnerFit
    """
    return round(0.50 * relationship + 0.30 * reliability + 0.20 * runnerfit, 2)


def apply_scores(
    participants_df: pd.DataFrame,
    features_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Apply all scoring rules to compute final rankings.
    """
    # Merge participant info with features
    df = participants_df.merge(features_df, on="username", how="left")
    
    # Fill missing feature values (engagement_rate 추가)
    feature_cols = ["avg_comments_12", "avg_likes_12", "comment_like_ratio", 
                    "low_comment_post_rate", "community_signal", "running_hashtag_rate",
                    "engagement_rate"]
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = df[col].fillna(0)
    
    # Compute scores
    df["relationship_score"] = df.apply(compute_relationship_score, axis=1)
    df["reliability_score"] = df.apply(compute_reliability_score, axis=1)
    df["runnerfit_score"] = df.apply(compute_runnerfit_score, axis=1)
    
    df["final_score"] = df.apply(
        lambda r: compute_final_score(
            r["relationship_score"], 
            r["reliability_score"], 
            r["runnerfit_score"]
        ), 
        axis=1
    )
    
    return df


def apply_hard_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply hard filters and create risk flags.
    
    Hard filters (move to excluded pool):
    - is_private = True
    - posts_90d == 0
    
    Risk flags (keep but mark):
    - post_count <= 3: "low_posts"
    
    Returns:
    - (main_pool, excluded_pool)
    """
    df = df.copy()
    
    # Create risk flags
    risk_flags = []
    for _, row in df.iterrows():
        flags = []
        if row.get("is_private", False):
            flags.append("private")
        if row.get("posts_90d", 0) == 0:
            flags.append("inactive_90d")
        if row.get("post_count", 0) <= 3:
            flags.append("low_posts")
        risk_flags.append("|".join(flags) if flags else "")
    
    df["risk_flag"] = risk_flags
    
    # Split into main and excluded pools
    excluded_mask = (df["is_private"] == True) | (df["posts_90d"] == 0)
    
    excluded_pool = df[excluded_mask].copy()
    main_pool = df[~excluded_mask].copy()
    
    return main_pool, excluded_pool


def create_rankings(
    main_pool: pd.DataFrame,
    excluded_pool: pd.DataFrame
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Create final rankings and output DataFrames.
    
    Returns:
    - ranking: Full ranking of main pool
    - shortlist: Top 40
    - winners_draft: Top 20 + 10 reserves
    """
    # Sort by final score (descending), then by risk_flag (empty first)
    main_pool = main_pool.sort_values(
        by=["final_score", "risk_flag"],
        ascending=[False, True]
    ).reset_index(drop=True)
    
    main_pool["rank"] = range(1, len(main_pool) + 1)
    
    # Define output columns
    output_cols = [
        "rank", "username", "relationship_score", "reliability_score", 
        "runnerfit_score", "final_score", "risk_flag",
        "avg_comments_12", "avg_likes_12", "low_comment_post_rate", 
        "running_hashtag_rate", "followers", "posts_90d"
    ]
    available_cols = [c for c in output_cols if c in main_pool.columns]
    
    ranking = main_pool[available_cols].copy()
    shortlist = ranking.head(40).copy()
    
    # Winners: Top 20 + 10 reserves
    winners = ranking.head(20).copy()
    winners["status"] = "winner"
    reserves = ranking.iloc[20:30].copy()
    reserves["status"] = "reserve"
    winners_draft = pd.concat([winners, reserves], ignore_index=True)
    
    return ranking, shortlist, winners_draft


if __name__ == "__main__":
    # Test scoring functions
    print("Testing scoring rules...")
    print(f"avg_comments 0.3 -> {score_avg_comments(0.3)}")  # 5
    print(f"avg_comments 3.5 -> {score_avg_comments(3.5)}")  # 35
    print(f"low_comment_rate 0.9 -> {score_low_comment_penalty(0.9)}")  # -15
    print(f"last_post_days 5 -> {score_last_post_days(5)}")  # 30
    print(f"posts_90d 8 -> {score_posts_90d(8)}")  # 20
    print(f"running_rate 0.6 -> {score_running_hashtag(0.6)}")  # 15
