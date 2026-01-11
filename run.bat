@echo off
chcp 65001 >nul
echo ========================================
echo 카카오톡 실시간 메시지 추출 프로그램
echo ========================================
echo.

REM Python 설치 확인
python --version >nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo Python 3.8 이상을 설치하세요.
    pause
    exit /b 1
)

REM 패키지 설치 확인
echo [1/3] 필수 패키지 확인 중...
pip show pywinauto >nul 2>&1
if errorlevel 1 (
    echo [설치] 필수 패키지 설치 중...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [오류] 패키지 설치 실패
        pause
        exit /b 1
    )
) else (
    echo [확인] 필수 패키지 설치됨
)

REM 카카오톡 실행 확인
echo [2/3] 카카오톡 프로세스 확인 중...
tasklist /FI "IMAGENAME eq KakaoTalk.exe" 2>NUL | find /I /N "KakaoTalk.exe">NUL
if errorlevel 1 (
    echo [경고] 카카오톡이 실행되지 않았습니다.
    echo 카카오톡을 먼저 실행하세요.
    pause
    exit /b 1
) else (
    echo [확인] 카카오톡 실행 중
)

REM 프로그램 실행
echo [3/3] 프로그램 시작...
echo.
python main.py

pause
