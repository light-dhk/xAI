# FastAPI Statistical Modeling & Simulation WebApp — 개발 Workflow (MVP → 배포)

> 1인 개발자 / localhost 데스크톱 웹앱 / FastAPI + VSCode + PyInstaller 전제

---

## 0. 사전 준비 (1회성 세팅)

```
git init
python -m venv .venv
.venv\Scripts\activate   (Windows)
pip install fastapi uvicorn pandas numpy scipy python-multipart pyinstaller
pip freeze > requirements.txt
```

- `.gitignore` 작성 (`.venv/`, `__pycache__/`, `dist/`, `build/`, `*.spec` 제외 여부는 취향)
- VSCode: Python interpreter를 `.venv`로 지정

---

## 1단계 — Flat 구조로 로직 검증 (Debug Phase)

**목표**: 통계/시뮬레이션 로직 자체가 맞는지 확인. 폴더 구조는 아직 신경 쓰지 않음.

```
mnsdev/
├── main.py
├── config.py
├── data_loader.py
├── data_store.py
├── simulation.py
├── routes.py
├── index.html
├── main.js
└── style.css
```

### 이 단계에서 할 일 (순서대로)
1. `simulation.py` 로직을 **FastAPI 없이 순수 함수**로 작성, `if __name__ == "__main__":` 블록에서 print/matplotlib으로 단독 검증
2. `data_loader.py` — pandas 로딩 함수 단독 테스트 (csv/excel)
3. `data_store.py` — in-memory dict로 세션 저장 (DB 없음)
4. `config.py` — pyinstaller 대응 경로 함수(`resource_path`)를 **이 시점에 미리 확정** (나중에 안 바꿔도 되게)
5. `routes.py` — 위 함수들을 엔드포인트로 연결 (파일 하나에 라우터 다 몰아넣어도 됨)
6. `main.py` — FastAPI 앱 조립, static mount, CORS
7. `index.html` + `main.js` — **디자인 없이** 업로드 버튼 + 결과 텍스트 출력만 (fetch 연결 검증용)

### 이 단계 판단 기준
- import는 전부 flat (`from simulation import run_simulation`) → 신경 쓸 것 없음
- 매 커밋마다 `uvicorn main:app --reload`로 브라우저에서 직접 눌러보며 확인

---

## 2단계 — Tree 구조 전환 시점 판단

다음 신호 중 **2개 이상** 해당되면 전환:

| 신호 | 확인 |
|---|---|
| 파일 개수 8~10개 초과 | ☐ |
| `routes.py`가 100줄 초과 | ☐ |
| 같은 기능이 여러 파일에 중복 등장 | ☐ |
| 테스트 코드(`tests/`)를 쓰기 시작 | ☐ |
| 기능이 2개 이상 도메인으로 분화 (업로드/시뮬레이션/리포트 등) | ☐ |

---

## 3단계 — Tree 구조로 리팩토링

### 최종 목표 구조 (MVP 실전 기준, `*` = 필수)

```
MnS/
├── .venv/                        *
├── app/                          *
│   ├── __init__.py               *
│   ├── main.py                   *   # FastAPI 앱 조립
│   ├── core/
│   │   └── config.py             *   # 경로 처리, 상수
│   ├── api/
│   │   ├── routes_data.py        *   # 업로드 API
│   │   └── routes_simulate.py    *   # 시뮬레이션 API
│   ├── services/
│   │   ├── data_loader.py        *
│   │   ├── data_store.py         *
│   │   └── simulation.py         *
│   ├── static/                   *
│   │   ├── index.html            *
│   │   ├── js/main.js            *
│   │   └── css/style.css
│   └── data/                          # 앱 내장 참조데이터 (필요시만)
├── sample_data/                       # 개발용 테스트 데이터 (배포 X)
├── tests/                             # 로직 안정화 후 추가
├── run.py                         *   # pyinstaller entry point
├── requirements.txt                *
├── .gitignore                     *
└── README.md
```

### 전환 작업 (30분~1시간 내 완료 가능)
```bash
mkdir -p app/api app/services app/core app/static/js app/static/css
mv routes.py → app/api/routes_*.py (기능별로 split)
mv simulation.py data_loader.py data_store.py → app/services/
mv config.py → app/core/
mv main.py → app/main.py
mv index.html main.js style.css → app/static/ (하위구조로)
```
- import 경로만 상대 → `app.services.xxx` 형태로 일괄 수정 (VSCode 리팩토링 or `sed`)
- `run.py` 신규 작성:
```python
from app.main import app
import uvicorn, webbrowser, threading

if __name__ == "__main__":
    port = 8000
    threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}")).start()
    uvicorn.run(app, host="127.0.0.1", port=port)
```

---

## 4단계 — 기능 확장 (필요할 때만 추가)

| 필요해지는 시점 | 추가할 것 |
|---|---|
| API 요청/응답 형식이 복잡해짐 | `models/schemas.py` (Pydantic) |
| 데이터를 세션 간 영구 보관해야 함 | `database.py` + SQLite |
| 외부 배포/다중 사용자 | `core/security.py` (인증) |
| 반복 회귀 방지 필요 | `tests/test_services.py`부터 시작 |
| 빌드 옵션이 반복적으로 복잡해짐 | `scripts/build.py` |

> 원칙: **미리 만들지 않는다 (YAGNI).** 필요해지는 신호가 보일 때 그 폴더만 추가.

---

## 5단계 — 통합 테스트 (배포 전)

1. `uvicorn app.main:app --reload`로 전체 시나리오 수동 재검증
2. Swagger(`/docs`)로 API 스펙 재확인
3. 엣지 케이스: 빈 파일 업로드, 잘못된 확장자, 대용량 파일 → try/except 방어 코드 확인

---

## 6단계 — PyInstaller 패키징

1. `.spec` 파일 작성 (또는 CLI 옵션 직접 지정)
```python
datas=[('app/static', 'app/static')]  # app/data 있으면 여기도 추가
```
2. **one-dir로 먼저 빌드** (디버깅 쉬움) → 안정화되면 one-file 전환
```bash
pyinstaller run.py --name MnS --add-data "app/static;app/static"
```
3. 빌드된 실행파일을 **다른 폴더로 옮겨서** 실행 → 경로 문제(`_MEIPASS`), static 파일 로딩, DB/캐시 생성 위치 확인
4. 콘솔 숨김(windowed) 모드 시 에러 로그 파일 기록 로직 점검

---

## 7단계 — 마무리 및 배포 부가 기능

- 아이콘, 트레이 아이콘
- 중복 실행 방지 (포트 점유 체크, lock file)
- 자동 브라우저 오픈 + 자유 포트(find_free_port) 처리
- README 작성 (실행 방법)

---

## 전체 흐름 요약도

```
[디버그 스크립트]
     ↓  로직 검증 (FastAPI 없음)
[Flat 구조: main.py + module.py들 + html/js/css]
     ↓  fetch 연결 확인, API 붙이기
[8~10개 파일 초과 / 역할 중복 발생]
     ↓  전환
[Tree 구조: app/api, app/services, app/core, app/static]
     ↓  필요시에만
[+ models, + database, + security, + tests]
     ↓
[통합 테스트 (uvicorn)]
     ↓
[PyInstaller 빌드 (.spec, one-dir → one-file)]
     ↓
[배포용 exe]
```

---

## 프로젝트 재사용 전략 (다음 프로젝트 시작 시)

| 상황 | 방식 |
|---|---|
| 완전히 다른 도메인 신규 프로젝트 | **템플릿 폴더** 복사 (뼈대만, 로직 없음) |
| 같은 카테고리(통계/시뮬레이션) 변형 프로젝트 | **기존 프로젝트 통째로 copy-paste** 후 도메인 로직만 교체 |

템플릿 폴더 예시 위치: `templates/fastapi-mvp-skeleton/` (config.py, run.py, .gitignore, main.py 뼈대만 포함)
