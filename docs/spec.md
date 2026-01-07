# 관계형 영향력 기반 러너 20명 선정 파이프라인 스펙

## 목적
Instagram 이벤트 게시물 댓글 참여자 중 **관계형 영향력**(댓글/대화/신뢰)이 높은 러너 20명 선정.

## 데이터 소스
3개 Instagram 이벤트 게시물:
- DSuGGGvDFB7
- DSuGISfjPUk  
- DSlsKZGE9KS

## 스코어링 체계
| 카테고리 | 배점 | 가중치 |
|---------|------|--------|
| Relationship | 0~50 | 50% |
| Reliability | 0~30 | 30% |
| RunnerFit | 0~20 | 20% |

## 출력
- `shortlist.csv`: Top 40
- `winners_draft.csv`: Top 20 + 예비 10명

## 실행
```bash
python -m src.pipeline
```
