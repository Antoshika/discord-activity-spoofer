import re

_PUNCT_RE = re.compile(r"[™®©:\-_.,!?'\"()\[\]]")
_WS_RE = re.compile(r"\s+")


def normalize_name(name: str) -> str:
    name = name.lower()
    name = _PUNCT_RE.sub(" ", name)
    return _WS_RE.sub(" ", name).strip()
