from fastapi import APIRouter
from src.modules.tenancy.router import router as tenancy_router
from src.modules.identity.router import router as identity_router
from src.modules.access.router import router as access_router
from src.modules.directory.router import router as directory_router
from src.modules.complaints.router import router as complaints_router
from src.modules.feedback.router import router as feedback_router
from src.modules.attendance.router import router as attendance_router
from src.api.dependencies import require_permission

api_router = APIRouter(prefix="/api/v1")

# Mount module routers
api_router.include_router(tenancy_router)
api_router.include_router(identity_router)
api_router.include_router(access_router)
api_router.include_router(directory_router)
api_router.include_router(complaints_router)
api_router.include_router(feedback_router)
api_router.include_router(attendance_router)



@api_router.get("/system/health", tags=["System"])
@require_permission("system:health")
def health_check():
    """System health check endpoint (Rule NR-8)."""
    return {
        "status": "healthy",
        "service": "CampusCare AI Core",
        "version": "1.0.0",
    }
