# 관계형 영향력 기반 선정 대시보드

인스타그램 이벤트 당첨자 선정을 위한 Streamlit 대시보드

## 실행 방법

```bash
# 패키지 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py
```

## 데이터 파일

| 파일 경로 | 설명 |
|-----------|------|
| `data/processed/ranking.csv` | 최종 랭킹 데이터 (필수) |
| `data/processed/posts_clean.csv` | 포스트 상세 데이터 (선택) |
| `data/processed/winners_draft.csv` | 임시 당첨자 목록 (대체용) |

## 기능

- **랭킹 테이블**: 필터/정렬 가능, 선정 체크박스
- **유저 상세 패널**: 최근 포스트, 리스크 플래그
- **Export**: 선정 20명 / 예비 10명 CSV 다운로드
- **사이드바 필터**: 비공개 제외, 활동 없는 계정 제외, Top N 조정
