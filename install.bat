@echo off
chcp 65001 >nul
echo ========================================
echo 카카오톡 메시지 추출 프로그램 설치
echo ========================================
echo.

REM Python 설치 확인
python --version
if errorlevel 1 (
    echo.
    echo [오류] Python이 설치되어 있지 않습니다.
    echo.
    echo 설치 방법:
    echo 1. https://www.python.org/downloads/ 방문
    echo 2. Python 3.8 이상 다운로드 및 설치
    echo 3. 설치 시 "Add Python to PATH" 체크
    echo.
    pause
    exit /b 1
)

echo.
echo [확인] Python 설치됨
echo.

REM pip 업그레이드
echo [1/2] pip 업그레이드 중...
python -m pip install --upgrade pip

REM 패키지 설치
echo.
echo [2/2] 필수 패키지 설치 중...
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [오류] 패키지 설치 실패
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 설치 완료!
echo ========================================
echo.
echo 사용 방법:
echo 1. 카카오톡을 실행하세요
echo 2. run.bat을 실행하세요
echo.
pause
