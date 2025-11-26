import time
import traceback
from app.core.logger import baemin_logger
from app.core.session import AsyncCurlClient
from app.core.cookie_store import save_cookie
from app.core.errors import (
    LoginError,
    StructureChangedError,
    RecaptchaError,
    BaeminError,
)
from app.crawler.utils import RSAEncryptor, generate_dummy_password


# -----------------------------
#   CONSTANTS
# -----------------------------
LOGIN_INIT_URL = "https://biz-member.baemin.com/v1/login/init"
LOGIN_URL = "https://biz-member.baemin.com/v1/login"

INIT_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://biz-member.baemin.com/login",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0",
}

LOGIN_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
    "Origin": "https://biz-member.baemin.com",
    "Referer": "https://biz-member.baemin.com/login",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:144.0) Gecko/20100101 Firefox/144.0",
}


# -----------------------------
#   STEP 1: TAG FETCH (RSA 초기화)
# -----------------------------
async def fetch_tag(session: AsyncCurlClient) -> str:
    """배민 로그인 초기화 → TAG 값 획득"""
    ts = round(time.time() * 1000)

    res, status = await session.get(
        LOGIN_INIT_URL,
        params={"__ts": ts},
        headers=INIT_HEADERS,
        body_type="JSON",
    )

    baemin_logger.info(f"[INIT] status={status}, res={res}")

    if status != 200:
        raise StructureChangedError("init API 실패: HTTP 200 아님")

    data = res.get("data", {})
    if data.get("needRecaptcha", False):
        raise RecaptchaError("배민이 Recaptcha 요구함")

    tag = data.get("tag")
    if not tag:
        raise StructureChangedError("TAG 없음 (구조 변경 가능성)")

    return tag


# -----------------------------
#   STEP 2: 로그인 + 쿠키 추출
# -----------------------------
async def login_and_get_cookie(id: str, pw: str, session: AsyncCurlClient) -> dict:
    """
    1) TAG 조회
    2) RSA 암호화
    3) 로그인 요청
    4) curl_cffi 쿠키 추출
    5) 쿠키 저장소에 저장
    """

    try:
        # --------------------------
        # 1) TAG 요청
        # --------------------------
        tag = await fetch_tag(session)

        # --------------------------
        # 2) RSA 암호화 준비
        # --------------------------
        n = int(tag, 16)
        rsa = RSAEncryptor(n)

        enc_id = rsa.encrypt(id)
        enc_pw = rsa.encrypt(pw)

        if not enc_id or not enc_pw:
            raise LoginError("RSA 암호화 실패")

        # --------------------------
        # 3) 로그인 요청 payload
        # --------------------------
        payload = {
            "id": id,
            "pw": generate_dummy_password(),  # 더미 PW
            "value1": enc_id,
            "value2": enc_pw,
            "token": "",
            "autoLogin": False,
        }

        login_url = f"{LOGIN_URL}?__ts={round(time.time() * 1000)}"

        # IMPORTANT: AsyncCurlClient.post()에서 원본 응답 r을 받을 수 있도록 return_response=True 사용
        res, status, r = await session.post(
            login_url,
            json_data=payload,
            headers=LOGIN_HEADERS,
            body_type="JSON",
            return_response=True,
        )

        baemin_logger.info(f"[LOGIN] status={status}, res={res}")

        if status != 200 or res.get("status") != "SUCCESS":
            raise LoginError("아이디 또는 패스워드 오류")

        # --------------------------
        # 4) curl_cffi 쿠키 추출
        # --------------------------
        raw_cookie_jar = r.cookies.jar  # RequestsCookieJar 객체

        cookies = {c.name: c.value for c in raw_cookie_jar}

        if "_ceo_v2_gk_sid" not in cookies:
            raise StructureChangedError("로그인 성공했지만 필수 쿠키 없음 → 구조 변경 가능성 있음")

        # --------------------------
        # 5) 파일 저장소에 저장
        # --------------------------
        save_cookie(id, cookies)
        baemin_logger.info(f"[COOKIE SAVED] account_id={id}")

        return cookies

    except Exception as e:
        baemin_logger.error("[LOGIN ERROR]")
        baemin_logger.error(traceback.format_exc())
        raise BaeminError(str(e))

async def login(id: str, pw: str) -> dict:
    """
    기존 FastAPI 라우터에서 쓰는 엔트리 포인트.

    - 내부에서 AsyncCurlClient 세션을 만들고
    - login_and_get_cookie를 호출한 뒤
    - 세션을 정리(cleanup)합니다.
    """
    session = AsyncCurlClient(
        timeout=30,
        impersonate="chrome",
        http_version="v1",
    )
    await session.start()

    try:
        cookies = await login_and_get_cookie(id, pw, session)
        return cookies
    finally:
        await session.close()