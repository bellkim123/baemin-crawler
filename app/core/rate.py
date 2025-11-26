# app/core/rate.py

import asyncio
import random
from functools import wraps


# 전역 세마포어 (동시 실행 개수 제어)
GLOBAL_RATE_SEMAPHORE = asyncio.Semaphore(3)


async def random_delay(min_ms: int = 200, max_ms: int = 800):
    """
    랜덤 딜레이 (반차단용)
    """
    delay = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
    await asyncio.sleep(delay)


def rate_limited(
    _func=None,
    *,
    semaphore: asyncio.Semaphore | None = None,
    min_ms: int = 200,
    max_ms: int = 800,
):
    """
    사용 예시
    --------
    1) 기본 사용
        @rate_limited
        async def fetch_page(...):
            ...

    2) 옵션 사용
        @rate_limited(semaphore=my_sem, min_ms=100, max_ms=500)
        async def fetch_page(...):
            ...
    """

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            sem = semaphore or GLOBAL_RATE_SEMAPHORE
            async with sem:
                await random_delay(min_ms=min_ms, max_ms=max_ms)
                return await func(*args, **kwargs)

        return wrapper

    # @rate_limited 처럼 인자 없이 쓴 경우
    if _func is not None and callable(_func):
        return decorator(_func)

    # @rate_limited(...) 처럼 옵션을 준 경우
    return decorator
