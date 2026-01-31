# Doubless Operation

센터 PC용 운영 시스템 - 업무일지 작성 및 데이터 추출

## 기능

- **업무일지**: 트레이너-회원 수업 기록 입력/관리
- **회원 동기화**: Broj CRM에서 회원 정보 불러오기
- **수강권 동기화**: CRM에서 수강권(PT) 정보 불러오기
- **데이터 내보내기**: JSON 형태로 내보내기 → doubless에서 임포트

## 설치

### Windows

```batch
# 1. 설치 스크립트 실행
scripts\install.bat

# 2. 환경 설정 확인
# backend\.env 파일에서 CRM 설정 확인

# 3. 실행
scripts\start.bat
```

### 개발 환경 (Mac/Linux)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일 설정
uvicorn app.main:app --reload --port 8000

# Frontend (별도 터미널)
cd frontend
npm install
npm run dev
```

## 사용법

1. **회원 동기화**: 회원/수강권 페이지에서 "회원 동기화", "수강권 동기화" 클릭
2. **수업 등록**: 업무일지 페이지에서 "수업 추가" 클릭
3. **데이터 내보내기**: 내보내기 페이지에서 기간 선택 후 "내보내기 실행"

## 내보내기 포맷

```json
{
  "export_info": {
    "export_id": "exp-20260131-180000",
    "center_name": "더블에스",
    "period": { "start_date": "2026-01-01", "end_date": "2026-01-31" }
  },
  "sessions": [
    {
      "session_date": "2026-01-15",
      "session_time": "10:00",
      "trainer_name": "김트레",
      "member_name": "이회원",
      "session_type": "PT",
      "session_status": "completed",
      "session_index": "15/20"
    }
  ],
  "statistics": { "total_sessions": 450, "completed": 420 }
}
```

## 기술 스택

- Backend: FastAPI + SQLite
- Frontend: React + Vite + TypeScript + Tailwind CSS v4
