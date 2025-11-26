# app/crawler/order_parser.py

from datetime import datetime
from app.models.order import (
    OrderRequest,
    PayInfo,
    OrderItem,
    Option,
    OptionCategory,
)


# --------- 안전 숫자 변환 헬퍼 ----------
def to_int(v):
    if v is None:
        return 0
    try:
        return int(v)
    except:
        return 0


def to_float(v):
    if v is None:
        return 0.0
    try:
        return float(v)
    except:
        return 0.0


# --------- 아이템 파싱 ----------
def parse_items(items):
    order_items = []
    preview = ""
    qty_sum = 0
    price_sum = 0

    if items and len(items) > 0:
        preview = items[0].get("name", "")
        if len(items) > 1:
            preview += f" 외 {len(items) - 1}건"

    for item in items or []:
        qty = to_int(item.get("quantity"))
        total = to_int(item.get("totalPrice"))
        unit = total / qty if qty > 0 else 0

        options_raw = item.get("options", []) or []

        options = [
            Option(
                option_id="",
                option_name=opt.get("name", ""),
                option_price=to_int(opt.get("price")),
                option_category=OptionCategory(
                    option_category_id="",
                    option_category_name=""
                ),
                option_qty=qty,
            )
            for opt in options_raw
        ]

        order_items.append(
            OrderItem(
                item_id="",
                item_name=item.get("name", ""),
                item_price=unit,
                item_qty=qty,
                option=options,
                coupon=[],
            )
        )

        qty_sum += qty
        price_sum += total

    return order_items, preview, qty_sum, price_sum

def parse_order(order, pid):
    items, preview, total_qty, items_total_price = parse_items(order.get("items"))

    delivery_tip = to_int(order.get("deliveryTip"))
    extra_tip = to_int(order.get("extraDeliveryTip"))
    discount_price = to_int(order.get("discountPrice"))
    pay_amount = to_int(order.get("payAmount"))

    total_price = items_total_price + delivery_tip + extra_tip - discount_price

    order_time_raw = order.get("orderDateTime")
    try:
        ts = int(datetime.fromisoformat(order_time_raw).timestamp())
    except:
        ts = 0

    # ---- 상태 매핑 ----
    baemin_status = order.get("status", "")
    status_code = map_status(baemin_status)

    pay_info = PayInfo(
        user_id=str(pid),
        tran_no="",
        tran_type="",
        total_amount=pay_amount,
        result_code="0000",
        approval_num="",
        approval_date="",
    )

    return OrderRequest(
        uid=str(pid),
        pid=str(pid),
        order_date=ts,
        pos_order_id="",
        order_delivery_id=order.get("orderNumber", ""),
        status=status_code,
        pg_status=status_code,
        order_path="direct",
        order_type=order.get("deliveryType", ""),
        pay_type="BAEMIN",

        total_price=total_price,
        pay_price=pay_amount,
        delivery_price=delivery_tip,

        order_item_qty=total_qty,
        order_info=items,
        order_item=preview,
        pay_info=pay_info,
    ).model_dump()

def map_status(status_str: str) -> int:
    mapping = {
        "ORDERED": 1,
        "ACCEPTED": 2,
        "PICKED_UP": 3,
        "DELIVERING": 4,
        "CLOSED": 5,
        "CANCELLED": 9,
    }
    return mapping.get(status_str.upper(), 0)   # 모르면 0
