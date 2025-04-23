from fastapi import APIRouter
from app.api import codebase_analyzer

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Code Insight API is running 🚀"}


# Include the codebase analyzer router
router.include_router(codebase_analyzer.router)
