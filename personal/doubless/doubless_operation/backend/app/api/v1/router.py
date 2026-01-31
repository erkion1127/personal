"""API 라우터 통합"""

from fastapi import APIRouter

from app.api.v1.endpoints import sessions, members, exports, dashboard, trainers, lesson_tickets

api_router = APIRouter()

api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"],
)

api_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"],
)

api_router.include_router(
    members.router,
    prefix="/members",
    tags=["members"],
)

api_router.include_router(
    trainers.router,
    tags=["trainers"],
)

api_router.include_router(
    lesson_tickets.router,
    prefix="/lesson-tickets",
    tags=["lesson-tickets"],
)

api_router.include_router(
    exports.router,
    prefix="/exports",
    tags=["exports"],
)
