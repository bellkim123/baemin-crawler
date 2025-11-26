# app/core/logger.py

import logging

baemin_logger = logging.getLogger("baemin-crawler")
baemin_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_formatter = logging.Formatter(
    fmt="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
console_handler.setFormatter(console_formatter)

if not baemin_logger.handlers:
    baemin_logger.addHandler(console_handler)

__all__ = ["baemin_logger"]
