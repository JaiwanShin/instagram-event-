# 스키마 필드 매핑 노트

## 입력 스키마 (data/raw/)

### comments.json
| 필드 | 타입 | 설명 | 대체 키 |
|------|------|------|---------|
| username | str | 댓글 작성자 | ownerUsername, user |
| comment_text | str | 댓글 내용 | text, body |
| tagged_users_count | int | 태그된 사용자 수 | mentions_count |
| post_shortcode | str | 게시물 식별자 | shortcode |

### profiles.json
| 필드 | 타입 | 설명 | 대체 키 |
|------|------|------|---------|
| username | str | 사용자명 | - |
| followers | int | 팔로워 수 | followersCount |
| following | int | 팔로잉 수 | followsCount |
| is_private | bool | 비공개 여부 | isPrivate |
| post_count | int | 게시물 수 | postsCount |
| bio | str | 자기소개 | biography |

### posts.json
| 필드 | 타입 | 설명 | 대체 키 |
|------|------|------|---------|
| username | str | 게시자 | ownerUsername |
| post_date | str | 게시일 | timestamp, taken_at |
| caption | str | 캡션 | - |
| like_count | int | 좋아요 수 | likesCount |
| comment_count | int | 댓글 수 | commentsCount |
| media_type | str | 미디어 타입 | type |
| hashtags | list | 해시태그 | - |

## 출력 스키마 (data/processed/)

### participants_clean.csv
username, is_private, followers, following, post_count, bio, last_post_date, last_post_days, posts_90d

### features.csv
username, avg_comments_12, avg_likes_12, comment_like_ratio, low_comment_post_rate, community_signal, running_hashtag_rate

### ranking.csv
username, relationship_score, reliability_score, runnerfit_score, final_score, risk_flag
