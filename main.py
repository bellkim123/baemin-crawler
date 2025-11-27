from fastapi import FastAPI
from app.api.login_api import router as login_router
from app.api.order_api import router as order_router

app = FastAPI(title="Baemin Crawler API", version="1.0.0")

# 라우터 등록
app.include_router(login_router, prefix="/baemin", tags=["Baemin Login"])
app.include_router(order_router, prefix="/baemin", tags=["Baemin Orders"])

# 실행 명령:
# uvicorn main:app --reload

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",      # ← uvicorn CLI에서 쓰던 것과 동일
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
