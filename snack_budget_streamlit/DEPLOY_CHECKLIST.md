# 배포 체크리스트

1. `snack_budget_streamlit/app.py`가 이 핫픽스 파일인지 확인
2. app.py 상단에 `from catalog import` 또는 `from snack_recommender import`가 없는지 확인
3. `snack_budget_streamlit/requirements.txt`가 `streamlit==1.61.1` 한 줄인지 확인
4. Streamlit Cloud Main file path가 `snack_budget_streamlit/app.py`인지 확인
5. GitHub 커밋이 main 브랜치에 반영됐는지 확인
6. Manage app → Reboot app 실행
7. 계속 실패하면 로그의 첫 번째 `ImportError:` 줄 전체를 확인
