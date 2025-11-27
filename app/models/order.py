from typing import List, Union
from pydantic import BaseModel


Number = Union[int, float]


class OptionCategory(BaseModel):
    option_category_id: str
    option_category_name: str


class Option(BaseModel):
    option_id: str
    option_name: str
    option_price: Number
    option_qty: int
    option_category: OptionCategory


class Coupon(BaseModel):
    coupon_id: str
    coupon_name: str
    discount_amount: Number


class OrderItem(BaseModel):
    item_id: str
    item_name: str
    item_price: Number
    item_qty: int
    option: List[Option]
    coupon: List[Coupon]


class PayInfo(BaseModel):
    user_id: str | int
    tran_no: str
    tran_type: str
    total_amount: Number
    result_code: str
    approval_num: str
    approval_date: str


class OrderRequest(BaseModel):
    uid: str                     # 점주 uid
    pid: str                     # 매장 pid (K034...)
    order_date: int              # Unix timestamp
    pos_order_id: str
    order_delivery_id: str       # 배민 주문번호
    status: int                  # 내부 주문 상태 코드
    pg_status: int               # 내부 PG 상태 코드
    order_path: str              # 'direct' 등
    order_type: str              # 'D' / 'T' / 'H'
    pay_type: str                # 'BAEMIN'
    total_price: Number          # 총 금액(배달비 포함)
    pay_price: Number            # 상품 금액 합
    delivery_price: Number       # 배달비
    order_item_qty: int          # 총 수량
    order_info: List[OrderItem]  # 상세 아이템 리스트
    order_item: str              # "아메리카노 외 2건" 같은 요약 문자열
    pay_info: PayInfo
