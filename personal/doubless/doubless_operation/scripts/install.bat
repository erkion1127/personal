@echo off
chcp 65001 > nul
echo ================================================
echo   더블에스 운영 시스템 설치
echo ================================================
echo.

REM 현재 스크립트 위치로 이동
cd /d "%~dp0.."

REM Python 가상환경 생성
echo [1/4] Python 가상환경 생성 중...
cd backend
python -m venv venv
if errorlevel 1 (
    echo Python 설치를 확인해주세요.
    pause
    exit /b 1
)

REM 패키지 설치
echo [2/4] Python 패키지 설치 중...
call venv\Scripts\activate.bat
pip install -r requirements.txt
if errorlevel 1 (
    echo 패키지 설치 실패
    pause
    exit /b 1
)

REM 환경 설정 파일 복사
echo [3/4] 환경 설정 파일 생성 중...
if not exist .env (
    copy .env.example .env
    echo .env 파일이 생성되었습니다. 설정을 확인해주세요.
)

REM 데이터 디렉토리 생성
echo [4/4] 데이터 디렉토리 생성 중...
cd ..
if not exist data mkdir data
if not exist data\exports mkdir data\exports

echo.
echo ================================================
echo   설치가 완료되었습니다!
echo.
echo   다음 단계:
echo   1. backend\.env 파일에서 CRM 설정 확인
echo   2. scripts\start.bat 실행
echo ================================================
pause
