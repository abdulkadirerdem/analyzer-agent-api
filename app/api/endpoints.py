from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {"message": "Code Insight API is running 🚀"}
