from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints import health, research, stream
from app.core.config import CORS_ORIGINS, ENVIRONMENT, HOST, PORT
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title="Being-Up-To-Date Assistant API",
    description="Backend for the Being-Up-To-Date Assistant MVP",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_origin_regex=r"https?://localhost:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(research.router, prefix="/api")
app.include_router(stream.router, prefix="/api")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Being-Up-To-Date Assistant API"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=HOST,
        port=PORT,
        reload=ENVIRONMENT == "development",
        timeout_keep_alive=120,  # 2 minutes for long-running research requests
    )




