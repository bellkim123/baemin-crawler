import traceback
from app.core.errors import BaeminError
from app.core.logger import baemin_logger
from app.core.session import AsyncCurlClient


async def fetch_account_number(cookies: dict, session: AsyncCurlClient) -> str:
    """사장님 계정 번호(shopOwnerNumber) 조회"""
    url = "https://self-api.baemin.com/v1/session/profile"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "service-channel": "SELF_SERVICE_PC",
        "Referer": "https://self.baemin.com/",
    }

    try:
        res, status = await session.get(
            url, headers=headers, cookies=cookies, body_type="JSON"
        )

        if status != 200:
            raise BaeminError("계정번호 조회 실패")

        account_no = res.get("shopOwnerNumber")
        if not account_no:
            raise BaeminError("shopOwnerNumber 조회 실패")

        return account_no

    except Exception:
        baemin_logger.error(f"[ACCOUNT ERROR] {traceback.format_exc()}")
        raise


async def fetch_shop_number(
    cookies: dict, account_number: str, session: AsyncCurlClient
) -> list:
    """해당 사장님 계정의 매장 목록 조회"""
    url = (
        "https://self-api.baemin.com/v4/store/shops/"
        "temporary-stop-status/by-shop-owner-number"
    )

    payload = {
        "shopOwnerNo": account_number,
        "lastOffsetId": "",
        "pageSize": 100,
        "desc": "true",
    }

    headers = {
        "Accept": "application/json, text/plain, */*",
        "service-channel": "SELF_SERVICE_PC",
        "Referer": "https://self.baemin.com/",
    }

    try:
        res, status = await session.get(
            url, headers=headers, params=payload, cookies=cookies, body_type="JSON"
        )

        if status != 200:
            raise BaeminError("매장 조회 실패")

        shops = res.get("content", [])
        return shops

    except Exception:
        baemin_logger.error(f"[SHOP ERROR] {traceback.format_exc()}")
        raise
