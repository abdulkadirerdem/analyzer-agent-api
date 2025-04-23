from fastapi import APIRouter

router = APIRouter()


@router.get("/analyze")
def analyze():
    return {"message": "Code Insight API is running 🚀"}
