import random
import traceback
from typing import Optional, Dict, Any

from curl_cffi.requests import AsyncSession
from aiolimiter import AsyncLimiter
from app.core.logger import baemin_logger


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) "
    "Gecko/20100101 Firefox/119.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:118.0) "
    "Gecko/20100101 Firefox/118.0",
]


class AsyncCurlClient:
    """
    curl_cffi 기반 비동기 HTTP 클라이언트
    - 랜덤 UA 지원
    - 쿠키 지원
    - 요청 레이트 제한
    - 프록시 지원
    - 요청/응답 상세 로깅
    """

    def __init__(
        self,
        timeout: int = 30,
        impersonate: str = "chrome",
        http_version: str = "v1",
        max_concurrent: int = 5,
        duration: int = 1,
        proxy: str | None = None,
    ):
        self.timeout = timeout
        self.impersonate = impersonate
        self.http_version = http_version
        self.proxy = proxy

        self.rate_limit = AsyncLimiter(max_concurrent, duration)
        self._session: Optional[AsyncSession] = None

    def random_ua(self) -> str:
        return random.choice(USER_AGENTS)

    async def start(self):
        if self._session is None:
            proxies = None
            if self.proxy:
                proxies = {
                    "http": self.proxy,
                    "https": self.proxy,
                }

            self._session = AsyncSession(
                timeout=self.timeout,
                impersonate=self.impersonate,
                http_version=self.http_version,
                proxies=proxies,
            )

    async def close(self):
        if self._session is not None:
            await self._session.close()
            self._session = None

    # ========================================================================
    # GET
    # ========================================================================
    async def get(
        self,
        url: str,
        headers: Dict[str, Any] | None = None,
        params: Dict[str, Any] | None = None,
        cookies: Dict[str, Any] | None = None,
        body_type: str = "JSON",
    ):
        if self._session is None:
            await self.start()

        headers = headers or {}
        headers.setdefault("User-Agent", self.random_ua())

        # 🔥 요청 로그
        baemin_logger.info(
            f"[HTTP GET REQUEST]\n"
            f"- URL: {url}\n"
            f"- Params: {params}\n"
            f"- Headers: {headers}\n"
            f"- Cookies: {cookies}\n"
            f"- Proxy: {self.proxy}\n"
        )

        try:
            async with self.rate_limit:
                r = await self._session.get(
                    url,
                    headers=headers,
                    params=params,
                    cookies=cookies,
                )

            raw = r.content.decode("utf-8", errors="ignore")

            # 🔥 응답 로그
            baemin_logger.info(
                f"[HTTP GET RESPONSE]\n"
                f"- URL: {url}\n"
                f"- Status: {r.status_code}\n"
                f"- RawBody: {raw[:800]}\n"
            )

            if body_type.upper() == "JSON":
                try:
                    return r.json(), r.status_code
                except Exception:
                    baemin_logger.error("[JSON PARSE ERROR - GET]")
                    baemin_logger.error(raw)
                    return {}, r.status_code

            return raw, r.status_code

        except Exception:
            baemin_logger.error("[HTTP GET ERROR]")
            baemin_logger.error(traceback.format_exc())
            return {}, 500

    # ========================================================================
    # POST
    # ========================================================================
    async def post(
        self,
        url: str,
        json_data: Dict[str, Any] | None = None,
        headers: Dict[str, Any] | None = None,
        cookies: Dict[str, Any] | None = None,
        body_type: str = "JSON",
        return_response: bool = False,
    ):
        if self._session is None:
            await self.start()

        headers = headers or {}
        headers.setdefault("User-Agent", self.random_ua())

        # 🔥 요청 로그
        baemin_logger.info(
            f"[HTTP POST REQUEST]\n"
            f"- URL: {url}\n"
            f"- JSON: {json_data}\n"
            f"- Headers: {headers}\n"
            f"- Cookies: {cookies}\n"
            f"- Proxy: {self.proxy}\n"
        )

        try:
            async with self.rate_limit:
                r = await self._session.post(
                    url,
                    json=json_data,
                    headers=headers,
                    cookies=cookies,
                )

            raw = r.content.decode("utf-8", errors="ignore")

            # 🔥 응답 로그
            baemin_logger.info(
                f"[HTTP POST RESPONSE]\n"
                f"- URL: {url}\n"
                f"- Status: {r.status_code}\n"
                f"- RawBody: {raw[:800]}\n"
            )

            if body_type.upper() == "JSON":
                try:
                    parsed = r.json()
                except Exception:
                    baemin_logger.error("[JSON PARSE ERROR - POST]")
                    baemin_logger.error(raw)
                    parsed = {}

            else:
                parsed = raw

            if return_response:
                return parsed, r.status_code, r
            return parsed, r.status_code

        except Exception:
            baemin_logger.error("[HTTP POST ERROR]")
            baemin_logger.error(traceback.format_exc())
            if return_response:
                return {}, 500, None
            return {}, 500
