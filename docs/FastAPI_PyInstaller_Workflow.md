# FastAPI + PyInstaller 빌드 워크플로우

FastAPI 앱을 PyInstaller로 단일 실행파일(.exe)로 패키징하기 위한 범용 가이드.
새 프로젝트를 시작할 때 이 문서를 그대로 복사해서 프로젝트 이름만 바꿔 쓰면 된다.

---

## 0. 왜 단순히 `pyinstaller main.py`로 안 되는가

FastAPI 자체는 문제 없지만, **uvicorn**이 내부적으로 프로토콜 구현체(`uvicorn.protocols.http.auto` 등)를
런타임에 동적으로 import하기 때문에 PyInstaller의 정적 분석(static analysis)이 이를 감지하지 못한다.
그 결과 빌드는 성공하지만 실행 시 `ModuleNotFoundError`가 발생하는 경우가 대부분이다.

또한 `StaticFiles`, `Jinja2Templates`가 참조하는 `"app/static"`, `"app/templates"` 같은
**상대경로**는, exe로 묶였을 때 실행 위치가 달라지면 100% 깨진다.

이 두 가지가 이 워크플로우의 핵심 문제이고, 아래 단계들은 전부 이 두 문제를 해결하기 위한 것이다.

---

## 1. 권장 프로젝트 구조

```
project/
├── .venv/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 인스턴스 (app = FastAPI())
│   ├── api/                 # 라우터
│   ├── core/                # 설정, 보안, DB 등
│   ├── services/            # 비즈니스 로직 (데이터 분석/시뮬레이션 등)
│   ├── static/               # JS, CSS, 이미지
│   └── templates/            # Jinja2 HTML
├── run.py                    # PyInstaller 진입점 (신규 생성)
├── requirements.txt
└── qapi_app.spec             # 1차 빌드 후 생성, 수정해서 재사용
```

핵심 규칙: **`app/` 안의 모듈에서 static/templates 경로를 참조할 때는 절대 상대경로를 쓰지 말고,
아래 2번의 `resource_path()` 헬퍼를 항상 통해서 접근한다.**

---

## 2. `app/main.py` — 경로 처리 헬퍼 (필수)

```python
import os
import sys

def resource_path(relative_path: str) -> str:
    """
    실행 환경에 따라 정확한 리소스 경로를 반환한다.
    - PyInstaller onefile로 실행된 경우: sys._MEIPASS (임시 압축해제 폴더) 기준
    - 일반 python 실행인 경우: 이 파일(main.py)이 위치한 폴더 기준
    """
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
```

사용 예:

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()
app.mount("/static", StaticFiles(directory=resource_path("static")), name="static")
templates = Jinja2Templates(directory=resource_path("templates"))
```

> 주의: `main.py`가 이미 `app/` 폴더 안에 있으므로, `resource_path("static")`이지
> `resource_path("app/static")`이 아니다. (자기 자신 기준 상대경로이기 때문)

---

## 3. `run.py` — PyInstaller 진입점 (프로젝트 루트에 생성)

```python
import uvicorn
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**왜 별도 진입점이 필요한가:**
- `uvicorn.run("app.main:app", ...)`처럼 **문자열**로 앱을 지정하면 PyInstaller 환경에서
  동적 임포트가 실패할 수 있다. `app` 객체를 직접 import해서 넘기는 방식이 안전하다.
- `reload=True`는 절대 쓰지 않는다. reload는 자식 프로세스를 spawn하는 방식인데,
  패키징된 exe 내부에서는 동작하지 않는다.

### (선택) 브라우저 자동 오픈

```python
import uvicorn
import webbrowser
import threading
from app.main import app

def open_browser():
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## 4. 패키지 설치

```powershell
pip install pyinstaller
pip install "uvicorn[standard]"
pip install jinja2 python-multipart python-dotenv   # 필요한 경우
```

> `requirements.txt`에 `uvicorn`만 있으면 부족하다. 반드시 `uvicorn[standard]`로 설치해야
> `httptools`, `websockets` 등 필요한 서브패키지가 함께 들어온다.

빌드 전 requirements.txt 갱신:

```powershell
pip freeze > requirements.txt
```

---

## 5. 먼저 일반 실행으로 검증 (PyInstaller 전 필수 단계)

```powershell
python run.py
```

`http://localhost:8000`에서 정상 동작 확인 후에만 다음 단계로 넘어간다.
이 단계를 건너뛰면 PyInstaller 문제인지 코드 문제인지 구분이 안 되어 디버깅이 배로 걸린다.

---

## 6. PyInstaller 1차 실행 (spec 파일 생성)

```powershell
pyinstaller --name qapi_app run.py
```

이 시점의 `dist\qapi_app\qapi_app.exe`는 대부분 실패한다 (정상). 목적은 실행파일이 아니라
`qapi_app.spec` 파일을 생성하는 것이다.

---

## 7. `qapi_app.spec` 수정 (핵심 단계)

`Analysis(...)` 블록의 `datas`와 `hiddenimports`만 수정한다. `pyz = PYZ(a.pure)` 이하는 건드리지 않는다.

```python
a = Analysis(
    ['run.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/static', 'static'),
        ('app/templates', 'templates'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
```

### `datas` 경로 표기법 이해하기

```python
('app/static', 'static'),
```

- **앞**: 현재 프로젝트 폴더 기준, 실제 파일이 있는 소스 경로
- **뒤**: exe 내부(`_MEIPASS`)에 심어질 타겟 경로

이게 2번의 `resource_path("static")` 호출과 정확히 짝이 맞아야 한다. 폴더 구조가 바뀌면
이 두 곳(spec의 datas, main.py의 resource_path 인자)을 항상 같이 맞춰야 한다.

### DB, 설정 파일 등 추가 리소스가 있다면

```python
datas=[
    ('app/static', 'static'),
    ('app/templates', 'templates'),
    ('app/data', 'data'),          # 예: 시뮬레이션 초기 데이터
    ('.env.example', '.'),          # 예: 환경변수 템플릿 (실제 .env는 넣지 않는 게 안전)
],
```

---

## 8. spec 기반 재빌드

```powershell
pyinstaller qapi_app.spec
```

기존 `dist\qapi_app\` 폴더를 덮어쓸지 물어보면 `y`로 진행 (이전 1차 빌드 산출물이므로 안전).

---

## 9. 실행 테스트

```powershell
.\dist\qapi_app\qapi_app.exe
```

`http://localhost:8000` 접속해서 확인.

콘솔에 아래처럼 뜨면 정상:

```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 10. (선택) onefile로 묶기

폴더 전체(`dist\qapi_app\`) 대신 실행파일 하나로 배포하고 싶은 경우:

```powershell
pyinstaller --onefile --name qapi_app `
  --add-data "app/static;static" `
  --add-data "app/templates;templates" `
  --hidden-import uvicorn.logging `
  --hidden-import uvicorn.loops.auto `
  --hidden-import uvicorn.protocols.http.auto `
  --hidden-import uvicorn.protocols.websockets.auto `
  --hidden-import uvicorn.lifespan.on `
  run.py
```

> Windows에서 `--add-data`의 구분자는 `;`, Linux/Mac은 `:`.
> PowerShell 줄바꿈은 백틱(`` ` ``) 사용.

**onefile의 단점**: 실행할 때마다 임시폴더에 압축을 풀기 때문에 시작 속도가 느리다.
서버처럼 한 번 켜서 계속 쓰는 앱이라면 폴더 방식(9번)이 더 낫다.

### 콘솔 창 없이 실행하고 싶다면

```powershell
pyinstaller --name qapi_app --windowed [...나머지 옵션 동일...] run.py
```

단, `--windowed`를 쓰면 uvicorn 로그를 콘솔에서 볼 수 없게 된다.
**개발/디버깅 중엔 콘솔 버전, 최종 배포용엔 windowed 버전을 따로 빌드하는 것을 권장.**

---

## 11. 흔한 문제 트러블슈팅

| 증상 | 원인 | 해결 |
|---|---|---|
| `ModuleNotFoundError: uvicorn.xxx` | uvicorn 동적 import 미탐지 | `hiddenimports`에 해당 모듈 추가 |
| static/templates 파일 안 보임 / `FileNotFoundError` | 상대경로 사용, 또는 spec의 datas 누락 | `resource_path()` 사용 + spec `datas` 확인 |
| exe 실행 시 창이 잠깐 떴다 사라짐 | 대부분 **정상 동작** (콘솔이 프로세스와 생명주기 공유) | `Get-Process <name>`으로 실제 실행 여부 확인. 크래시가 의심되면 bat 파일 + `pause`로 로그 확인 |
| reload 관련 에러 | `uvicorn.run(..., reload=True)` 설정 | `reload=False` (또는 옵션 자체 제거) |
| 다른 PC에서 실행 안 됨 | `dist\qapi_app\` 폴더를 통째로 옮기지 않고 exe만 옮김 | 폴더 전체 복사 (dll, `_internal` 등 포함) |
| 포트 충돌 | 8000번 포트를 다른 프로세스가 점유 중 | `netstat -ano | findstr :8000` 으로 확인 후 종료 |

---

## 12. 실행/종료 관련 PowerShell 명령 모음

```powershell
# 실행 중인지 확인
Get-Process qapi_app -ErrorAction SilentlyContinue

# 상세 정보와 함께 확인
Get-Process qapi_app -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, CPU, WS

# 특정 포트 점유 프로세스 확인
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
netstat -ano | findstr :8000

# 종료
Stop-Process -Id <PID>
Get-Process qapi_app -ErrorAction SilentlyContinue | Stop-Process
```

**콘솔 창을 X로 닫으면 프로세스도 함께 종료된다** (Windows의 `CTRL_CLOSE_EVENT` 기본 동작).
백그라운드로 계속 띄워두고 싶다면 콘솔을 닫지 말고 최소화하거나, `--windowed` 빌드 + 작업관리자로
프로세스를 직접 관리하는 방식을 사용한다.

---

## 13. 체크리스트 (새 프로젝트 시작 시)

- [ ] `app/main.py`에 `resource_path()` 헬퍼 추가
- [ ] `StaticFiles`, `Jinja2Templates`의 `directory=` 인자를 `resource_path(...)`로 감싸기
- [ ] 프로젝트 루트에 `run.py` 생성, `app` 객체 직접 import
- [ ] `uvicorn.run(..., reload=False)` 확인
- [ ] `requirements.txt`에 `uvicorn[standard]` 명시
- [ ] `python run.py`로 먼저 정상 동작 확인
- [ ] `pyinstaller --name <앱이름> run.py`로 1차 빌드 (spec 생성 목적)
- [ ] `.spec`의 `datas`, `hiddenimports` 수정
- [ ] `pyinstaller <앱이름>.spec`으로 재빌드
- [ ] `dist\<앱이름>\<앱이름>.exe` 실행 테스트
- [ ] 배포 시 `dist\<앱이름>\` **폴더 전체** 복사 (exe만 X)
- [ ] 인증 정보(`AUTH_USER`, `AUTH_PASS` 등) 기본값을 배포 전 반드시 변경했는지 확인
