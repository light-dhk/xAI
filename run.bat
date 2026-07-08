@echo off
cd /d "%~dp0"

echo ============================================
echo   xAIPM 실행 준비 중...
echo ============================================

REM 1. Python 설치 여부 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 Python을 설치한 뒤
    echo 설치 시 "Add Python to PATH" 옵션을 반드시 체크해 주세요.
    pause
    exit /b 1
)

REM 2. 필요 패키지 설치 (이미 설치돼 있으면 빠르게 스킵됨)
echo 필요한 라이브러리를 확인/설치합니다...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [오류] 라이브러리 설치 중 문제가 발생했습니다.
    pause
    exit /b 1
)

REM 3. streamlit 실행 (python -m 방식으로 PATH 문제 회피)
echo 프로그램을 실행합니다...
python -m streamlit run xAIPM.py

pause
