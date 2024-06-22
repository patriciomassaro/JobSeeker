from functools import partial
import re
import base64

_snake_1 = partial(re.compile(r"(.)((?<![^A-Za-z])[A-Z][a-z]+)").sub, r"\1_\2")
_snake_2 = partial(re.compile(r"([a-z0-9])([A-Z])").sub, r"\1_\2")


def snake_case(string: str) -> str:
    return _snake_2(_snake_1(string)).casefold()


def encode_pdf_to_base64(pdf_bytes: bytes | None) -> str | None:
    if pdf_bytes:
        return base64.b64encode(pdf_bytes).decode("utf-8")
    return None


def decode_base64_to_pdf(b64_string: str | None) -> bytes | None:
    if b64_string:
        return base64.b64decode(b64_string)
    return None
