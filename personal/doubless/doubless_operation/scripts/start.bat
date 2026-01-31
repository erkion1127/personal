@echo off
chcp 65001 > nul
echo ================================================
echo   더블에스 운영 시스템 시작
echo ================================================
echo.

REM 현재 스크립트 위치로 이동
cd /d "%~dp0.."

REM Backend 시작
echo [1/2] Backend 서버 시작 중...
cd backend
start /B cmd /c "venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002"

REM 잠시 대기
timeout /t 3 /nobreak > nul

REM 브라우저 열기
echo [2/2] 브라우저 열기...
start http://localhost:8002

echo.
echo ================================================
echo   서버가 시작되었습니다!
echo   브라우저: http://localhost:8000
echo   종료하려면 이 창을 닫으세요.
echo ================================================
pause
