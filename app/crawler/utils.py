import os
import random
import string


class RSAEncryptor:
    """
    배민 로그인에 필요한 RSA-PKCS#1 v1.5 암호화기
    """

    def __init__(self, n: int, e: int = 65537):
        self.n = n
        self.e = e
        self.key_length = (n.bit_length() + 7) // 8  # RSA key size (bytes)

    def _pkcs1_pad(self, data: bytes, target_length: int) -> bytes:
        """
        PKCS#1 v1.5 padding
        구조: 0x00 02 [랜덤 non-zero 패딩] 00 [데이터]
        """

        data_len = len(data)
        if target_length < data_len + 11:
            return None

        padding_len = target_length - data_len - 3  # 00 02 + 패딩 + 00 + data

        padding = bytearray()
        while len(padding) < padding_len:
            b = os.urandom(1)[0]
            if b != 0:    # non-zero만 사용
                padding.append(b)

        return b"\x00\x02" + bytes(padding) + b"\x00" + data

    def encrypt(self, text: str) -> str:
        if not text:
            return ""

        data = text.encode("utf-8")

        padded = self._pkcs1_pad(data, self.key_length)
        if padded is None:
            return ""

        m = int.from_bytes(padded, "big")
        c = pow(m, self.e, self.n)

        hex_str = hex(c)[2:].lower()
        return hex_str if len(hex_str) % 2 == 0 else "0" + hex_str


def generate_dummy_password(length=60):
    chars = string.digits + string.ascii_lowercase
    return "".join(random.choice(chars) for _ in range(length))
