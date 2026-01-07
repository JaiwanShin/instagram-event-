"""
관계형 영향력 기반 선정 대시보드
Instagram 이벤트 당첨자 선정을 위한 Streamlit 대시보드
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

# 페이지 설정
st.set_page_config(
    page_title="관계형 영향력 기반 선정 대시보드",
    page_icon="🏃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 경로 상수
DATA_DIR = "data/processed"
RANKING_PATH = os.path.join(DATA_DIR, "ranking.csv")
WINNERS_DRAFT_PATH = os.path.join(DATA_DIR, "winners_draft.csv")
POSTS_PATH = os.path.join(DATA_DIR, "posts_clean.csv")

# 필요 컬럼 정의
# CSV 컬럼명 기준 (팔로워 바로 뒤에 평균 좋아요/댓글)
RANKING_COLUMNS = [
    "username", "is_private", "followers", "avg_likes_5", "avg_comments_5",
    "last_post_days", "posts_90d", "comment_like_ratio", "low_comment_post_rate",
    "running_hashtag_rate", 
    "Relationship", "Reliability", "RunnerFit", "Final",
    "risk_flags"
]

# UI용 컬럼 매핑
COLUMN_MAPPING = {
    "relationship_score": "Relationship",
    "reliability_score": "Reliability",
    "runnerfit_score": "RunnerFit",
    "final_score": "Final",
    "risk_flag": "risk_flags"
}

POST_COLUMNS = [
    "username", "date", "caption", "comments_count", "likes_count", "media_type", "is_running_related",
    "post_date", "comment_count", "like_count", "post_url"
]


def generate_sample_data() -> pd.DataFrame:
    """샘플 데이터 생성 (데이터가 없을 때 앱 동작 보장)"""
    import numpy as np
    np.random.seed(42)
    
    n_samples = 50
    usernames = [f"runner_{i:03d}" for i in range(n_samples)]
    
    data = {
        "username": usernames,
        "is_private": np.random.choice([True, False], n_samples, p=[0.1, 0.9]),
        "followers": np.random.randint(100, 50000, n_samples),
        "last_post_days": np.random.randint(0, 90, n_samples),
        "posts_90d": np.random.randint(0, 30, n_samples),
        "avg_comments_12": np.round(np.random.uniform(0, 50, n_samples), 1),
        "avg_likes_12": np.round(np.random.uniform(10, 500, n_samples), 1),
        "comment_like_ratio": np.round(np.random.uniform(0, 0.3, n_samples), 3),
        "low_comment_post_rate": np.round(np.random.uniform(0, 1, n_samples), 2),
        "running_hashtag_rate": np.round(np.random.uniform(0, 1, n_samples), 2),
        "Relationship": np.round(np.random.uniform(0, 100, n_samples), 1),
        "Reliability": np.round(np.random.uniform(0, 100, n_samples), 1),
        "RunnerFit": np.round(np.random.uniform(0, 100, n_samples), 1),
        "Final": np.round(np.random.uniform(0, 100, n_samples), 1),
        "risk_flags": np.random.choice(
            ["", "낮은_댓글수", "비활동", "낮은_댓글수,비활동", "러닝_컨텐츠_부족"],
            n_samples,
            p=[0.5, 0.15, 0.15, 0.1, 0.1]
        ),
        "post_count": np.random.randint(1, 100, n_samples)
    }
    
    df = pd.DataFrame(data)
    df = df.sort_values("Final", ascending=False).reset_index(drop=True)
    return df


def generate_sample_posts(usernames: list) -> pd.DataFrame:
    """샘플 포스트 데이터 생성"""
    import numpy as np
    np.random.seed(42)
    
    posts = []
    for username in usernames[:20]:  # 상위 20명만
        n_posts = np.random.randint(3, 15)
        for i in range(n_posts):
            days_ago = np.random.randint(0, 90)
            posts.append({
                "username": username,
                "date": (datetime.now() - pd.Timedelta(days=days_ago)).strftime("%Y-%m-%d"),
                "caption": f"오늘도 러닝 완료! 🏃 #{np.random.choice(['러닝', '달리기', '마라톤', '조깅'])}",
                "comments_count": np.random.randint(0, 100),
                "likes_count": np.random.randint(10, 1000),
                "media_type": np.random.choice(["image", "video", "carousel"]),
                "is_running_related": np.random.choice([True, False], p=[0.7, 0.3])
            })
    
    return pd.DataFrame(posts)


@st.cache_data
def load_ranking_data() -> tuple[pd.DataFrame, str]:
    """
    랭킹 데이터 로드 (Cache Reset v9 - low_frequency 플래그 추가)
    """
    if os.path.exists(RANKING_PATH):
        try:
            df = pd.read_csv(RANKING_PATH)
            
            # 컬럼 매핑 (실제 데이터 -> 앱 기준)
            rename_map = {
                "relationship_score": "Relationship",
                "reliability_score": "Reliability",
                "runnerfit_score": "RunnerFit",
                "final_score": "Final",
                "risk_flag": "risk_flags"
            }
            df = df.rename(columns=rename_map)
            
            # 필수 컬럼 채우기 (없는 경우)
            if "is_private" not in df.columns:
                df["is_private"] = False  # 기본값
            if "last_post_days" not in df.columns:
                df["last_post_days"] = 0  # 기본값
            if "avg_likes_12" not in df.columns:
                df["avg_likes_12"] = 0.0
            if "comment_like_ratio" not in df.columns:
                df["comment_like_ratio"] = 0.0
            if "low_comment_post_rate" not in df.columns:
                df["low_comment_post_rate"] = 0.0
                
            # 필요 컬럼만 선택 (존재하는 컬럼만)
            available_cols = [col for col in RANKING_COLUMNS if col in df.columns]
            # 추가로 필요한 원본 컬럼이 있다면 유지
            df = df[available_cols] if available_cols else df
            
            # 텍스트 컬럼 결측치 처리 (데이터 에디터 오류 방지)
            if "risk_flags" in df.columns:
                df["risk_flags"] = df["risk_flags"].fillna("").astype(str)
                # "nan" 문자열로 변환된 경우 다시 빈 문자열로
                df["risk_flags"] = df["risk_flags"].replace("nan", "")
            
            # 포스트 데이터가 있으면 누락된 메트릭 계산
            posts_df = load_posts_data()
            if posts_df is not None:
                df = calculate_metrics(df, posts_df)
                
            return df, "ranking"
        except Exception as e:
            st.error(f"ranking.csv 로드 오류: {e}")
            return pd.DataFrame(), "error"


def calculate_metrics(ranking_df: pd.DataFrame, posts_df: pd.DataFrame) -> pd.DataFrame:
    """포스트 데이터를 기반으로 누락된 메트릭 계산 (v2 - 음수값 필터링)"""
    ranking_df = ranking_df.copy()
    posts_df = posts_df.copy()
    
    # 음수값(-1) 필터링: 수집 실패한 데이터
    if "likes_count" in posts_df.columns:
        posts_df.loc[posts_df["likes_count"] < 0, "likes_count"] = pd.NA
    if "comments_count" in posts_df.columns:
        posts_df.loc[posts_df["comments_count"] < 0, "comments_count"] = pd.NA
    
    # 날짜 컬럼 변환
    if "date" in posts_df.columns:
        posts_df["date"] = pd.to_datetime(posts_df["date"], errors='coerce')
    
    for idx, row in ranking_df.iterrows():
        username = row["username"]
        user_posts = posts_df[posts_df["username"] == username]
        
        if len(user_posts) == 0:
            continue
            
        # 날짜 정렬 (최신순)
        if "date" in user_posts.columns:
            user_posts = user_posts.sort_values("date", ascending=False)
            
            # last_post_days 계산
            last_date = user_posts.iloc[0]["date"]
            if pd.notna(last_date):
                days_diff = (datetime.now(last_date.tzinfo) - last_date).days
                ranking_df.at[idx, "last_post_days"] = days_diff
        
        # 최근 5개 포스트 기준 집계 (수집 데이터 기준)
        recent_posts = user_posts.head(5)
        
        # Avg Likes (음수 제외하고 평균 계산)
        if "likes_count" in recent_posts.columns:
            valid_likes = recent_posts["likes_count"].dropna()
            avg_likes = valid_likes.mean() if len(valid_likes) > 0 else 0
        else:
            avg_likes = 0
        ranking_df.at[idx, "avg_likes_5"] = round(avg_likes, 1) if pd.notna(avg_likes) else 0
        
        # Avg Comments (음수 제외)
        if "comments_count" in recent_posts.columns:
            valid_comments = recent_posts["comments_count"].dropna()
            avg_comments = valid_comments.mean() if len(valid_comments) > 0 else 0
        else:
            avg_comments = 0
        ranking_df.at[idx, "avg_comments_5"] = round(avg_comments, 1) if pd.notna(avg_comments) else 0
        
        # Comment/Like Ratio
        if avg_likes > 0:
            ratio = avg_comments / avg_likes
            ranking_df.at[idx, "comment_like_ratio"] = round(ratio, 3)
        else:
            ranking_df.at[idx, "comment_like_ratio"] = 0
            
        # Low Comment Rate (댓글 3개 이하 비율)
        if "comments_count" in recent_posts.columns:
            valid_comments_df = recent_posts[recent_posts["comments_count"].notna()]
            low_comment_count = len(valid_comments_df[valid_comments_df["comments_count"] <= 3])
            low_rate = low_comment_count / len(valid_comments_df) if len(valid_comments_df) > 0 else 0
        else:
            low_rate = 0
        ranking_df.at[idx, "low_comment_post_rate"] = round(low_rate, 2)
        
        # Running Hashtag Rate (전체 기준)
        if "is_running_related" in user_posts.columns:
            run_count = user_posts["is_running_related"].sum()
            run_rate = run_count / len(user_posts)
            ranking_df.at[idx, "running_hashtag_rate"] = round(run_rate, 2)
        
        # 게시물 빈도 체크 (5개 게시물이 365일 이상에 걸쳐있으면 플래그)
        if "date" in recent_posts.columns and len(recent_posts) >= 2:
            dates = recent_posts["date"].dropna()
            if len(dates) >= 2:
                newest = dates.iloc[0]
                oldest = dates.iloc[-1]
                if pd.notna(newest) and pd.notna(oldest):
                    date_span = (newest - oldest).days
                    if date_span > 365:
                        # 리스크 플래그에 추가
                        current_flags = str(ranking_df.at[idx, "risk_flags"]) if pd.notna(ranking_df.at[idx, "risk_flags"]) else ""
                        if "low_frequency" not in current_flags:
                            new_flags = f"{current_flags}|low_frequency" if current_flags else "low_frequency"
                            ranking_df.at[idx, "risk_flags"] = new_flags
            
    return ranking_df


@st.cache_data
def load_posts_data() -> pd.DataFrame | None:
    """포스트 데이터 로드 (Cache Reset v4)"""
    if os.path.exists(POSTS_PATH):
        try:
            df = pd.read_csv(POSTS_PATH)
            
            # 컬럼 매핑 (원본 -> 통일된 이름)
            rename_map = {
                "post_date": "date",
                "like_count": "likes_count",
                "comment_count": "comments_count"
            }
            df = df.rename(columns=rename_map)
            
            # Running Related 계산 (없으면)
            if "is_running_related" not in df.columns:
                keywords = ["러닝", "달리기", "마라톤", "run", "조깅", "running", "트레일", "울트라"]
                def check_running(row):
                    text = str(row.get("caption", "")) + str(row.get("hashtags", ""))
                    return any(k.lower() in text.lower() for k in keywords)
                
                df["is_running_related"] = df.apply(check_running, axis=1)
            
            # 모든 컬럼 반환 (필터링 제거)
            return df
        except Exception as e:
            st.warning(f"포스트 데이터 로드 중 오류: {e}")
            return None
    return None


def apply_filters(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    """필터 적용"""
    filtered = df.copy()
    
    # 비공개 제외
    if filters.get("exclude_private", True) and "is_private" in filtered.columns:
        filtered = filtered[~filtered["is_private"]]
    
    # posts_90d == 0 제외
    if filters.get("exclude_no_posts", True) and "posts_90d" in filtered.columns:
        filtered = filtered[filtered["posts_90d"] > 0]
    

    
    # Top N 적용
    top_n = filters.get("top_n", 40)
    if len(filtered) > top_n:
        filtered = filtered.head(top_n)
    
    return filtered.reset_index(drop=True)


def get_exceptions(df: pd.DataFrame) -> pd.DataFrame:
    """예외풀 (비공개 계정) 반환"""
    if "is_private" in df.columns:
        return df[df["is_private"]].reset_index(drop=True)
    return pd.DataFrame()


def to_csv_download(df: pd.DataFrame) -> bytes:
    """DataFrame을 CSV 바이트로 변환"""
    return df.to_csv(index=False).encode("utf-8-sig")


def main():
    st.title("🏃 관계형 영향력 기반 선정 대시보드")
    
    # 데이터 로드
    df, data_source = load_ranking_data()
    posts_df = load_posts_data()
    
    # 데이터 소스에 따른 안내 메시지
    if data_source == "sample":
        st.warning("""
        ⚠️ **데이터가 없습니다!**
        
        `data/processed/ranking.csv` 또는 `data/processed/winners_draft.csv`가 없어 **샘플 데이터**로 표시 중입니다.
        
        👉 데이터 파이프라인을 실행하여 실제 데이터를 생성해주세요.
        """)
        # 샘플 포스트 데이터도 생성
        if posts_df is None:
            posts_df = generate_sample_posts(df["username"].tolist())
    elif data_source == "winners_draft":
        st.info("""
        ℹ️ `ranking.csv`가 없어 `winners_draft.csv`로 표시 중입니다.
        
        전체 랭킹을 보려면 파이프라인을 실행하여 `ranking.csv`를 생성하세요.
        """)
    
    # ========== 사이드바 ==========
    with st.sidebar:
        st.header("🔧 필터 설정")
        
        st.subheader("하드 필터")
        exclude_private = st.toggle("비공개 계정 제외", value=True)
        exclude_no_posts = st.toggle("posts_90d=0 제외", value=True)
        exclude_low_frequency = st.toggle("자동 선정 제외 (low_frequency risk)", value=True)
        show_low_post_warning = st.toggle("post_count≤3 경고 표시", value=True)
        
        st.divider()
        
        top_n = st.slider("Top N 표시", min_value=10, max_value=100, value=40, step=5)
        
        st.divider()
        
        show_exceptions = st.toggle("예외풀 (비공개) 보기", value=False)
    
    # 필터 적용
    filters = {
        "exclude_private": exclude_private,
        "exclude_no_posts": exclude_no_posts,
        "exclude_low_frequency": exclude_low_frequency,
        "top_n": top_n
    }
    
    filtered_df = apply_filters(df, filters)
    
    # ========== 선정 상태 관리 ==========
    # 자동 선정 로직
    def auto_select():
        # 후보군 추출 (필터링된 전체 리스트에서 시작)
        candidates_df = filtered_df.copy()
        
        # low_frequency 제외 (자동 선정 시에만 제외)
        if exclude_low_frequency and "risk_flags" in candidates_df.columns:
            candidates_df = candidates_df[~candidates_df["risk_flags"].str.contains("low_frequency", na=False)]
        
        # 상위 20명/10명 선정
        current_candidates = candidates_df["username"].tolist()
        st.session_state.selected_users = set(current_candidates[:20])
        st.session_state.backup_users = set(current_candidates[20:30])
        st.toast("✅ 상위 20명(선정) / 10명(예비) 자동 선택 완료!")

    # 초기화 또는 버튼 클릭 시
    if "selected_users" not in st.session_state:
        st.session_state.selected_users = set()
        st.session_state.backup_users = set()
        auto_select()  # 첫 로드 시 자동 선정
    
    with st.sidebar:
        st.divider()
        if st.button("🔄 자동 선정 적용 (Top 20+10)", use_container_width=True):
            auto_select()
            st.rerun()

    # ========== 메인 컨텐츠 ==========
    
    # 탭 구성
    if show_exceptions:
        tab1, tab2 = st.tabs(["📊 랭킹 테이블", "🔒 예외풀 (비공개)"])
    else:
        tab1 = st.container()
        tab2 = None
    
    # ----- 랭킹 테이블 탭 -----
    with tab1 if show_exceptions else st.container():
        st.subheader(f"📊 랭킹 테이블 (Top {len(filtered_df)}명)")
        
        # 선정 체크박스 컬럼 추가
        display_df = filtered_df.copy()
        display_df.insert(0, "선정", False)
        display_df.insert(1, "예비", False)
        
        # 기존 선택 상태 복원
        display_df["선정"] = display_df["username"].isin(st.session_state.selected_users)
        display_df["예비"] = display_df["username"].isin(st.session_state.backup_users)
        
        # post_count 경고 표시
        if show_low_post_warning and "post_count" in display_df.columns:
            display_df["⚠️"] = display_df["post_count"].apply(lambda x: "⚠️" if x <= 3 else "")
        
        # 데이터 에디터로 표시
        column_config = {
            "선정": st.column_config.CheckboxColumn("선정 (20)", default=False),
            "예비": st.column_config.CheckboxColumn("예비 (10)", default=False),
            "username": st.column_config.TextColumn("유저네임", width="medium"),
            "is_private": st.column_config.CheckboxColumn("비공개", disabled=True),
            "followers": st.column_config.NumberColumn("팔로워", format="%d"),
            "avg_likes_5": st.column_config.NumberColumn("평균좋아요", format="%.1f"),
            "avg_comments_5": st.column_config.NumberColumn("평균댓글", format="%.1f"),
            "last_post_days": st.column_config.NumberColumn("최근활동(일)", format="%d"),
            "posts_90d": st.column_config.NumberColumn("90일포스트", format="%d"),
            "comment_like_ratio": st.column_config.NumberColumn("댓글/좋아요비율", format="%.3f"),
            "low_comment_post_rate": st.column_config.NumberColumn("저댓글비율", format="%.2f"),
            "running_hashtag_rate": st.column_config.NumberColumn("러닝태그율", format="%.2f"),
            "Final": st.column_config.ProgressColumn("Final", min_value=0, max_value=100, format="%.1f"),
            "Relationship": st.column_config.ProgressColumn("Relationship", min_value=0, max_value=100, format="%.1f"),
            "Reliability": st.column_config.ProgressColumn("Reliability", min_value=0, max_value=100, format="%.1f"),
            "RunnerFit": st.column_config.ProgressColumn("RunnerFit", min_value=0, max_value=100, format="%.1f"),
            "risk_flags": st.column_config.TextColumn("리스크", width="medium"),
        }
        
        # 컬럼 순서 지정 (팔로워 다음에 평균 좋아요/댓글)
        column_order = [
            "선정", "예비", "username", "is_private", "followers", 
            "avg_likes_5", "avg_comments_5",
            "last_post_days", "posts_90d", "comment_like_ratio", "low_comment_post_rate",
            "running_hashtag_rate", "Relationship", "Reliability", "RunnerFit", "Final", "risk_flags"
        ]
        
        edited_df = st.data_editor(
            display_df,
            column_config=column_config,
            column_order=column_order,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed",
            key="ranking_table"
        )
        
        # 선택 상태 업데이트
        selected_users = set(edited_df[edited_df["선정"]]["username"].tolist())
        backup_users = set(edited_df[edited_df["예비"]]["username"].tolist())
        
        st.session_state.selected_users = selected_users
        st.session_state.backup_users = backup_users
        
        # 선택 수 표시 및 경고
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_count = len(selected_users)
            if selected_count > 20:
                st.error(f"⚠️ 선정 인원 초과! ({selected_count}/20)")
            else:
                st.info(f"선정: {selected_count}/20")
        
        with col2:
            backup_count = len(backup_users)
            if backup_count > 10:
                st.error(f"⚠️ 예비 인원 초과! ({backup_count}/10)")
            else:
                st.info(f"예비: {backup_count}/10")
        
        with col3:
            overlap = selected_users & backup_users
            if overlap:
                st.warning(f"⚠️ 중복 선택: {', '.join(overlap)}")
    
    # ----- 예외풀 탭 -----
    if show_exceptions and tab2 is not None:
        with tab2:
            exceptions_df = get_exceptions(df)
            if len(exceptions_df) > 0:
                st.subheader(f"🔒 예외풀 - 비공개 계정 ({len(exceptions_df)}명)")
                st.dataframe(exceptions_df, use_container_width=True, hide_index=True)
            else:
                st.info("예외풀에 해당하는 계정이 없습니다.")
    
    st.divider()
    
    # ========== 유저 상세 패널 ==========
    st.subheader("👤 유저 상세 정보")
    
    # 유저 선택
    all_usernames = filtered_df["username"].tolist()
    if all_usernames:
        selected_username = st.selectbox(
            "유저 선택",
            options=all_usernames,
            index=0,
            key="user_select"
        )
        
        # 해당 유저 정보
        user_info = filtered_df[filtered_df["username"] == selected_username].iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**📊 기본 정보**")
            st.metric("Final Score", f"{user_info.get('Final', 'N/A'):.1f}" if pd.notna(user_info.get('Final')) else "N/A")
            
            metrics_col1, metrics_col2 = st.columns(2)
            with metrics_col1:
                st.metric("Relationship", f"{user_info.get('Relationship', 'N/A'):.1f}" if pd.notna(user_info.get('Relationship')) else "N/A")
                st.metric("Reliability", f"{user_info.get('Reliability', 'N/A'):.1f}" if pd.notna(user_info.get('Reliability')) else "N/A")
            with metrics_col2:
                st.metric("RunnerFit", f"{user_info.get('RunnerFit', 'N/A'):.1f}" if pd.notna(user_info.get('RunnerFit')) else "N/A")
                st.metric("팔로워", f"{user_info.get('followers', 'N/A'):,}" if pd.notna(user_info.get('followers')) else "N/A")
            
            
            
            st.markdown("**📈 활동 지표 (최근 5개)**")
            act_col1, act_col2, act_col3 = st.columns(3)
            with act_col1:
                st.metric("평균 좋아요", f"{user_info.get('avg_likes_5', 0):.1f}")
            with act_col2:
                st.metric("평균 댓글", f"{user_info.get('avg_comments_5', 0):.1f}")
            with act_col3:
                ratio = float(user_info.get('comment_like_ratio', 0))
                st.metric("소통의 질", f"{ratio*100:.1f}%", help="댓글/좋아요 비율")

            st.divider()
            # 프로필 링크 버튼
            st.link_button("🌐 인스타그램 프로필 방문", f"https://www.instagram.com/{selected_username}/", use_container_width=True)
            st.divider()
            
            # 리스크 플래그 표시
            risk_flags = user_info.get("risk_flags", "")
            if risk_flags and str(risk_flags) != "nan":
                st.markdown("**🚨 리스크 플래그**")
                flags = str(risk_flags).split(",")
                for flag in flags:
                    flag = flag.strip()
                    if flag:
                        st.warning(f"• {flag}")
            else:
                st.success("✅ 리스크 플래그 없음")
        
        with col2:
            st.markdown("**📝 최근 포스트**")
            # st.caption("※ 데이터에 개별 게시물 링크 정보가 없어 프로필 링크로 대체합니다.")
            
            # 러닝 관련 필터
            show_running_only = st.toggle("러닝 관련 포스트만 보기", value=False, key="running_filter")
            
            if posts_df is not None and len(posts_df) > 0:
                user_posts = posts_df[posts_df["username"] == selected_username].copy()
                
                if show_running_only and "is_running_related" in user_posts.columns:
                    user_posts = user_posts[user_posts["is_running_related"] == True]
                
                if len(user_posts) > 0:
                    # 날짜 정렬
                    if "date" in user_posts.columns:
                        user_posts = user_posts.sort_values("date", ascending=False)
                    
                    # 음수값(-1)을 0으로 변환 (수집 실패 데이터)
                    if "likes_count" in user_posts.columns:
                        user_posts.loc[user_posts["likes_count"] < 0, "likes_count"] = 0
                    if "comments_count" in user_posts.columns:
                        user_posts.loc[user_posts["comments_count"] < 0, "comments_count"] = 0
                    
                    # 캡션 자르기
                    if "caption" in user_posts.columns:
                        user_posts["caption_preview"] = user_posts["caption"].apply(
                            lambda x: str(x)[:50] + "..." if pd.notna(x) and len(str(x)) > 50 else str(x) if pd.notna(x) else ""
                        )
                    
                    # 표시할 컬럼 선택
                    display_cols = []
                    if "date" in user_posts.columns:
                        display_cols.append("date")
                    if "caption_preview" in user_posts.columns:
                        display_cols.append("caption_preview")
                    if "comments_count" in user_posts.columns:
                        display_cols.append("comments_count")
                    if "likes_count" in user_posts.columns:
                        display_cols.append("likes_count")
                    if "media_type" in user_posts.columns:
                        display_cols.append("media_type")
                    if "post_url" in user_posts.columns:
                        display_cols.append("post_url")
                    
                    if display_cols:
                        st.dataframe(
                            user_posts[display_cols].head(10),
                            use_container_width=True,
                            hide_index=True,
                            column_config={
                                "date": st.column_config.TextColumn("날짜"),
                                "caption_preview": st.column_config.TextColumn("캡션", width="large"),
                                "comments_count": st.column_config.NumberColumn("댓글"),
                                "likes_count": st.column_config.NumberColumn("좋아요"),
                                "media_type": st.column_config.TextColumn("타입"),
                                "post_url": st.column_config.LinkColumn("링크", display_text="🔗 이동")
                            }
                        )
                    else:
                        st.info("표시할 포스트 컬럼이 없습니다.")
                else:
                    st.info("해당 유저의 포스트가 없거나 필터 조건에 맞는 포스트가 없습니다.")
            else:
                st.info("📭 포스트 데이터가 없습니다. `data/processed/posts_clean.csv`를 생성하세요.")
    else:
        st.info("표시할 유저가 없습니다.")
    
    st.divider()
    
    # ========== Export 섹션 ==========
    st.subheader("📥 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 선정 20명 다운로드
        if selected_users:
            selected_df = df[df["username"].isin(selected_users)]
            st.download_button(
                label=f"🏆 선정 {len(selected_users)}명 CSV 다운로드",
                data=to_csv_download(selected_df),
                file_name=f"selected_winners_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                disabled=len(selected_users) > 20
            )
            if len(selected_users) > 20:
                st.caption("⚠️ 20명 이하로 선정해주세요")
        else:
            st.button("🏆 선정 0명 (선택 필요)", disabled=True)
    
    with col2:
        # 예비 10명 다운로드
        if backup_users:
            backup_df = df[df["username"].isin(backup_users)]
            st.download_button(
                label=f"📋 예비 {len(backup_users)}명 CSV 다운로드",
                data=to_csv_download(backup_df),
                file_name=f"backup_winners_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                disabled=len(backup_users) > 10
            )
            if len(backup_users) > 10:
                st.caption("⚠️ 10명 이하로 선정해주세요")
        else:
            st.button("📋 예비 0명 (선택 필요)", disabled=True)
    
    with col3:
        # 전체 랭킹 다운로드
        st.download_button(
            label=f"📊 전체 랭킹 CSV ({len(filtered_df)}명)",
            data=to_csv_download(filtered_df),
            file_name=f"full_ranking_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    st.divider()
    
    # ========== 스코어 산출 공식 설명 ==========
    with st.expander("ℹ️ 스코어 산출 공식 및 로직 설명"):
        st.markdown("""
        ### 필터링 및 점수 산출 로직
        
        본 대시보드는 **관계형 영향력(Relational Influence)**을 중심으로 진정성 있는 러너를 선정합니다.
        
        #### 1. 주요 지표 (Scores)
        
        - **Relationship (관계성, 50점 만점)**
          **평균 댓글 수**에 따른 기본 점수에서, **소통 부재(댓글 3개 이하 게시물 비율)**에 따른 페널티를 적용합니다.
          > `평균 댓글 수 구간 점수(최대 50점) - 소통 부재 페널티(최대 -15점)`
          
        - **Reliability (신뢰성, 30점 만점)**
          **최근 활동일(Recency)**과 **90일 내 포스팅 수(Frequency)**를 종합 평가하며, 비공개 계정은 감점합니다.
          > `(최근 활동 점수 + 활동 빈도 점수) / 2 - 비공개 감점`
          
        - **RunnerFit (러닝 적합도, 20점 만점)**
          게시물 중 **러닝 관련 콘텐츠(캡션, 해시태그)**의 비중이 얼마나 높은지 평가합니다.
          > `러닝 관련 포스트 수 / 전체 수집 포스트 수`
          
        - **Final Score (100점)**
          위 3가지 지표의 합산 점수입니다.
          > `Final = Relationship + Reliability + RunnerFit`
        
        #### 2. 메트릭 계산 기준 (Metrics)
        
        | 메트릭 | 한글명 | 계산 방법 | 해석 |
        |--------|--------|-----------|------|
        | **avg_likes_5** | 평균좋아요 | 최근 5개 게시물의 좋아요 평균 | 콘텐츠 인기도 |
        | **avg_comments_5** | 평균댓글 | 최근 5개 게시물의 댓글 평균 | 팔로워 참여도 |
        | **comment_like_ratio** | 댓글/좋아요비율 | 평균댓글 ÷ 평균좋아요 | 높을수록 소통 활발 (0.05 이상 권장) |
        | **low_comment_post_rate** | 저댓글비율 | 댓글 3개 이하 게시물 / 전체 5개 | 낮을수록 좋음 (0이면 모든 글에 댓글 4개+) |
        | **running_hashtag_rate** | 러닝태그율 | 러닝 관련 게시물 / 전체 게시물 | 1.0이면 100% 러닝 계정 |
        
        #### 3. 리스크 플래그 (Risk Flags)
        - **low_frequency**: 최근 5개 게시물의 날짜 범위가 365일 이상 (1년에 5개 이하 포스팅)
        """)


if __name__ == "__main__":
    main()
