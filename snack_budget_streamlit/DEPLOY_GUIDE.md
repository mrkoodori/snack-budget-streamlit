# GitHub 및 Streamlit 배포 적용 가이드

## 1. 백업

현재 저장소에서 작업 브랜치를 하나 만듭니다.

```bash
git checkout -b feature/daily-budget-10000-v3
```

## 2. 파일 교체

압축파일 안의 내용을 기존 저장소의 아래 폴더에 덮어씁니다.

```text
snack_budget_streamlit/
```

핵심 교체 파일:

```text
app.py
catalog.py
snack_recommender.py
tests/test_recommender.py
README.md
```

추가 파일:

```text
CHANGELOG.md
DEPLOY_GUIDE.md
```

## 3. 로컬 테스트

```bash
cd snack_budget_streamlit
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

확인 항목:

1. 교육시간 입력이 사라졌는지
2. 교육일수 1~5일 입력이 보이는지
3. 30명·5일·10,000원 선택 시 총예산 상한이 1,500,000원인지
4. 1인 누적 상한이 50,000원인지
5. 1인 1일 예산을 10,000원까지 선택할 수 있는지
6. 일자별 다과 구성이 순환되는지
7. 모든 추천 금액이 총예산 상한 이내인지
8. 쿠팡 검색 버튼이 정상적으로 열리는지
9. 구매 구성표와 일자별 운영안 CSV가 내려받아지는지

## 4. 커밋 및 푸시

```bash
git add snack_budget_streamlit
git commit -m "1인 1일 예산 상한을 10000원으로 확대"
git push -u origin feature/daily-budget-10000-v3
```

검토 후 기본 브랜치에 병합합니다.

## 5. Streamlit Community Cloud

기존 앱이 기본 브랜치와 연결되어 있으면 병합 후 자동 재배포됩니다.
자동 반영되지 않으면 앱 관리 화면에서 Reboot 또는 Redeploy를 실행합니다.

진입 파일은 저장소 구조에 따라 아래처럼 설정합니다.

```text
snack_budget_streamlit/app.py
```

## 6. 되돌리기

문제가 있으면 기존 커밋으로 되돌립니다.

```bash
git revert <병합 커밋 해시>
git push
```
