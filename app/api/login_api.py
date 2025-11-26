from fastapi import APIRouter
from pydantic import BaseModel
from app.crawler.login import login

router = APIRouter()

class LoginRequest(BaseModel):
    id: str
    pw: str

@router.post("/login")
async def login_api(body: LoginRequest):
    cookies = await login(body.id, body.pw)
    return {
        "code": 200,
        "message": "login success",
        "cookies": cookies
    }
