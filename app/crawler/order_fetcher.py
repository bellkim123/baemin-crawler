import asyncio
from app.core.rate import rate_limited, random_delay
from app.core.errors import BaeminError

ORDER_URL = "https://self-api.baemin.com/v4/orders"


async def fetch_orders(session, cookies, shop_owner_no, shop_no, start, end, status):
    """
    한 매장의 주문 전체 조회 (페이지네이션 자동 처리)
    """
    limit = 100

    headers = {
        "accept": "application/json, text/plain, */*",
        "origin": "https://self.baemin.com",
        "service-channel": "SELF_SERVICE_PC",
        "User-Agent": session.random_ua(),   # 랜덤 UA
    }

    # --------------------------
    # 1) 첫 페이지 조회 → totalSize 조회
    # --------------------------
    first_payload = {
        "offset": 0,
        "limit": limit,
        "purchaseType": "",
        "startDate": start,
        "endDate": end,
        "shopOwnerNumber": shop_owner_no,
        "shopNumbers": shop_no,
        "orderStatus": status,
    }

    res, sc = await session.get(
        ORDER_URL,
        headers=headers,
        params=first_payload,
        cookies=cookies
    )

    if sc != 200:
        raise BaeminError(500, f"[주문 조회 실패] HTTP {sc}")

    total = res.get("totalSize", 0)
    if total <= 0:
        return []

    total_pages = (total + limit - 1) // limit

    # --------------------------
    # 2) 전체 페이지 async 조회
    # --------------------------
    tasks = []
    for page in range(total_pages):
        offset = page * limit
        tasks.append(
            fetch_page(
                session,
                headers,
                cookies,
                shop_owner_no,
                shop_no,
                start,
                end,
                status,
                offset,
            )
        )

    all_results = await asyncio.gather(*tasks)

    # --------------------------
    # 3) 결과 머지
    # --------------------------
    merged = []
    for r in all_results:
        if r:
            merged.extend(r)

    return merged


@rate_limited        # ← 반차단 + 랜덤 딜레이 적용
async def fetch_page(
    session,
    headers,
    cookies,
    shop_owner_no,
    shop_no,
    start,
    end,
    status,
    offset
):
    """
    개별 페이지 조회
    """
    payload = {
        "offset": offset,
        "limit": 100,
        "purchaseType": "",
        "startDate": start,
        "endDate": end,
        "shopOwnerNumber": shop_owner_no,
        "shopNumbers": shop_no,
        "orderStatus": status,
    }

    res, sc = await session.get(
        ORDER_URL,
        headers=headers,
        params=payload,
        cookies=cookies
    )

    if sc != 200:
        raise BaeminError(500, f"[페이지 조회 실패] offset={offset}, HTTP {sc}")

    return res.get("contents", []) or []
