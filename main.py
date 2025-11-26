from fastapi import FastAPI
from app.api.login_api import router as login_router
from app.api.order_api import router as order_router

app = FastAPI(title="Baemin Crawler API", version="1.0.0")

# 라우터 등록
app.include_router(login_router, prefix="/baemin", tags=["Baemin Login"])
app.include_router(order_router, prefix="/baemin", tags=["Baemin Orders"])

# 실행 명령:
# uvicorn main:app --reload
