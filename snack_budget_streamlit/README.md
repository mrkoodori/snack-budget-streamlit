# v4.1 단일 파일 ImportError 핫픽스

## v4.2 적용 사항

- 1인 1일 예산 상한을 1,000원부터 최대 10,000원까지 직접 설정할 수 있습니다.
- 1일 8종, 2일 10종, 3일 12종, 4일 14종, 5일 16종은 후보 풀이 아니라 실제 최종 구매 다과 품목 수입니다.
- 교육일수가 길어질수록 프리미엄 품목에 가성비 품목을 더하며, 각 일자별 추천안도 설정한 1인 1일 예산 상한을 넘지 않도록 계산합니다.

이 배포본은 `catalog.py`와 `snack_recommender.py`를 import하지 않습니다.
상품 카탈로그, 추천 엔진, Streamlit 화면이 모두 `app.py` 한 파일에 들어 있습니다.

## 가장 빠른 적용

GitHub의 `snack_budget_streamlit/app.py`를 이 폴더의 `app.py`로 교체하고,
같은 폴더의 `requirements.txt`도 함께 교체한 뒤 커밋합니다.

기존 `catalog.py`와 `snack_recommender.py`는 남아 있어도 실행에 영향을 주지 않습니다.
혼동을 막으려면 삭제해도 됩니다.

## Streamlit Cloud 설정

- Repository: `mrkoodori/snack-budget-streamlit`
- Branch: `main`
- Main file path: `snack_budget_streamlit/app.py`
- Python: 3.12 권장
- requirements 위치: `snack_budget_streamlit/requirements.txt`

커밋 후 Streamlit Cloud에서 **Manage app → Reboot app**을 실행하세요.
Python 버전을 변경해야 하는 경우에는 기존 앱을 삭제하고 Python 3.12로 다시 배포해야 합니다.
