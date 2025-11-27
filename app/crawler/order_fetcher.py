import asyncio
from app.core.rate import rate_limited, random_delay
from app.core.errors import BaeminError

ORDER_URL = "https://self-api.baemin.com/v4/orders"


def is_block_page(raw: str) -> bool:
    """
    배민 보안 위배 페이지 HTML 탐지
    """
    if "<title>보안 위배" in raw:
        return True
    if "올바르지 않은 요청으로 페이지를 보실 수 없습니다" in raw:
        return True
    if "<!DOCTYPE html>" in raw and "보안" in raw:
        return True
    return False


async def fetch_orders(session, cookies, shop_owner_no, shop_no, start, end, status):
    """
    한 매장의 주문 전체 조회 (페이지네이션 자동 처리)
    """
    limit = 100

    headers = {
        "accept": "application/json, text/plain, */*",
        "origin": "https://self.baemin.com",
        "service-channel": "SELF_SERVICE_PC",
        "User-Agent": session.random_ua(),
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

    # 🔥 보안위배 감지
    if sc == 403 and is_block_page(str(res)):
        raise BaeminError(403, "[보안 위배] 배민이 접근을 차단했습니다.")

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


@rate_limited
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

    # 🔥 보안 위배 감지
    if sc == 403 and is_block_page(str(res)):
        raise BaeminError(403, "[보안 위배] 배민 보안 페이지 감지됨")

    if sc != 200:
        raise BaeminError(500, f"[페이지 조회 실패] offset={offset}, HTTP {sc}")

    return res.get("contents", []) or []
