from fastapi import APIRouter
from app.api import codebase_analyzer, analyzer_agent

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Code Insight API is running 🚀"}


# Include the codebase analyzer router
router.include_router(codebase_analyzer.router)

# Include the code explainer agent router
router.include_router(analyzer_agent.router)
