# Streamlit Community Cloud 배포

1. 압축파일을 풉니다.
2. GitHub 저장소의 `snack_budget_streamlit` 폴더 내용을 이 폴더의 파일로 덮어씁니다.
3. 아래 명령으로 로컬 테스트합니다.

```bash
pip install -r requirements.txt
python -m unittest discover -s tests -v
streamlit run app.py
```

4. GitHub에 커밋·푸시합니다.
5. Streamlit Community Cloud에서 Main file path가 다음인지 확인합니다.

```text
snack_budget_streamlit/app.py
```

6. 앱을 재부팅하거나 Reboot app을 실행합니다.

## 배포 후 확인

- 인원수 입력란이 한 개만 보이는지
- 고급 설정이 사라졌는지
- 음료 체크박스 세 개가 모두 해제 상태로 시작하는지
- 1/2/3/4/5일 선택 시 후보 풀이 8/10/12/14/16종인지
- 결과 페이지 상단에 쿠팡 홈 버튼이 보이는지
- 구매 구성과 후보 풀의 쿠팡 링크가 열리는지
