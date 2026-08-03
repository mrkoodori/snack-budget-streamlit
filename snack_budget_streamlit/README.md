# 예산 맞춤형 교육용 다과 추천 Streamlit 앱

사내 교육, 워크숍, 세미나, 연수, 설명회에서 여러 명에게 빠르게 배포하기 좋은
가성비 중심의 낱개포장 과자와 음료를 추천하는 웹앱입니다.

## 주요 기능

- 인원수, 음료 포함 여부, 주 연령대 3개 기본 입력
- 1인당 최대 5,000원 이내 예산 계산
- 다과 10~20% 여유 수량 및 음료 최소 인원분 계산
- 연령대별 추천 우선순위 적용
- 품목별 예상 단가, 예상 금액, ±10~15% 가격 오차범위
- 총예산 초과 자동 방지 및 소규모·복수 음료 경계 사례 자동 조정
- 쿠팡 검색 키워드와 검색 링크 자동 생성
- 구매 체크리스트
- CSV 구성표와 Markdown 추천서 다운로드
- 자동결제·로그인·장바구니·주문 대행 없음

## 프로젝트 구조

```text
.
├── app.py
├── catalog.py
├── snack_recommender.py
├── requirements.txt
├── Dockerfile
├── .gitignore
├── .streamlit/
│   └── config.toml
└── tests/
    └── test_recommender.py
```

## 로컬 실행

Python 3.10 이상을 사용합니다. 권장 버전은 Python 3.12입니다.

```bash
python -m venv .venv
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

설치 및 실행:

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 기본적으로 `http://localhost:8501`을 엽니다.

## 테스트

표준 라이브러리 `unittest`만 사용하므로 별도 테스트 패키지가 필요하지 않습니다.

```bash
python -m unittest discover -s tests -v
```

## Streamlit Community Cloud 배포

1. 이 프로젝트 파일을 새 GitHub 저장소에 올립니다.
2. Streamlit Community Cloud에 GitHub 계정으로 로그인합니다.
3. 워크스페이스 우측 상단의 **Create app**을 선택합니다.
4. 저장소, 브랜치, 진입 파일 `app.py`를 지정합니다.
5. Python 버전은 로컬 개발 환경과 같은 버전을 선택합니다. 권장: 3.12.
6. **Deploy**를 누릅니다.

이 앱은 외부 API 키가 없어 `secrets.toml`이 필요하지 않습니다.
`requirements.txt`는 저장소 루트에 두어야 합니다.

## Docker 실행

```bash
docker build -t snack-budget-app .
docker run --rm -p 8501:8501 snack-budget-app
```

브라우저에서 `http://localhost:8501`을 엽니다.

## 가격 데이터 수정

`catalog.py`의 각 상품에 있는 `pack_options`를 수정하면 추천 금액이 바뀝니다.

예:

```python
PackOption(24, 12_500)
```

위 값은 `24개입 묶음의 예상 가격이 12,500원`이라는 뜻입니다.
실시간 가격이 아니므로 운영 시 월 1회 또는 행사 전 가격을 점검하는 방식을 권장합니다.

## 운영상 주의

- 쿠팡 검색 결과의 판매가, 입수량, 재고, 배송일은 수시로 바뀔 수 있습니다.
- 앱의 가격은 구매 판단을 돕는 추정치이며 결제 금액을 보장하지 않습니다.
- 상품 상세 페이지에서 개별포장 여부, 유통기한, 여름철 보관 조건을 확인하세요.
- 쿠팡 페이지 스크래핑이나 자동 주문 로직은 포함하지 않았습니다.
