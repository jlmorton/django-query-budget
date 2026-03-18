from __future__ import annotations
import re

_STRING_RE = re.compile(r"'(?:[^']|'')*'")
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
_IN_LIST_RE = re.compile(r"\bIN\s*\(\s*\?(?:\s*,\s*\?)*\s*\)", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

def fingerprint_sql(sql: str, *, lowercase: bool = True) -> str:
    if not sql:
        return ""
    result = _STRING_RE.sub("?", sql)
    result = _NUMBER_RE.sub("?", result)
    result = _IN_LIST_RE.sub("IN (?)", result)
    result = _WHITESPACE_RE.sub(" ", result).strip()
    if lowercase:
        result = result.lower()
    return result
