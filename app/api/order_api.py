from fastapi import APIRouter
from pydantic import BaseModel

from app.core.session import AsyncCurlClient
from app.core.cookie_store import load_cookie
from app.crawler.login import login_and_get_cookie
from app.crawler.order_info import fetch_account_number, fetch_shop_number
from app.crawler.order_fetcher import fetch_orders
from app.crawler.order_parser import parse_order


class BaeminOrderRequest(BaseModel):
    id: str
    pw: str
    start: str
    end: str


router = APIRouter(prefix="/baemin")


@router.post("/orders")
async def get_orders(body: BaeminOrderRequest):
    session = AsyncCurlClient()
    await session.start()

    cookies = load_cookie(body.id)
    if cookies is None:
        cookies = await login_and_get_cookie(body.id, body.pw, session)

    account_no = await fetch_account_number(cookies, session)
    shops = await fetch_shop_number(cookies, account_no, session)

    shop_nos = [s["shopNo"] for s in shops]

    all_orders = []
    statuses = ["ACCEPTED", "CLOSED", "CANCELLED"]

    for shop_no in shop_nos:
        for st in statuses:
            rows = await fetch_orders(
                session,
                cookies,
                account_no,
                shop_no,
                body.start,
                body.end,
                st,
            )
            for item in rows:
                parsed = parse_order(item["order"], pid=shop_no)
                all_orders.append(parsed)

    await session.close()
    return {"code": 200, "data": all_orders}
