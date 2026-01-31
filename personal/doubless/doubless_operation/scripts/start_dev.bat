@echo off
chcp 65001 > nul
echo ================================================
echo   더블에스 운영 시스템 (개발 모드)
echo ================================================
echo.

cd /d "%~dp0.."

REM Backend 시작
echo [1/2] Backend 시작...
cd backend
start cmd /k "venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --port 8000"

REM Frontend 시작
echo [2/2] Frontend 시작...
cd ..\frontend
start cmd /k "npm run dev"

echo.
echo ================================================
echo   개발 서버가 시작되었습니다!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo ================================================
