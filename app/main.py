from fastapi import FastAPI
from app.api import endpoints

app = FastAPI(
    title="Code Insight API",
    description="This API provides static analysis and natural language annotation for Python files.",
    version="1.0.0",
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

app.include_router(endpoints.router)
