from __future__ import annotations
import copy
import hashlib
import ipaddress
import re
from typing import Any

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_MAC_RE = re.compile(r"\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b")
_IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

def _stable_token(value: str, label: str) -> str:
    digest = hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()[:10]
    return f"<{label}:{digest}>"

def redact_text(text: str, mode: str = "standard") -> str:
    if mode == "none":
        return text
    text = _EMAIL_RE.sub(lambda m: _stable_token(m.group(0), "email"), text)
    text = _MAC_RE.sub(lambda m: _stable_token(m.group(0), "mac"), text)

    def repl_ipv4(match: re.Match[str]) -> str:
        raw = match.group(0)
        try:
            addr = ipaddress.ip_address(raw)
        except ValueError:
            return raw
        if addr.is_loopback:
            return raw
        if mode == "strict":
            return _stable_token(raw, "ip")
        if addr.is_private:
            parts = raw.split(".")
            return ".".join(parts[:2] + ["x", "x"])
        return _stable_token(raw, "ip")

    return _IPV4_RE.sub(repl_ipv4, text)

def redact_payload(payload: Any, mode: str = "standard") -> Any:
    if mode == "none":
        return copy.deepcopy(payload)
    if isinstance(payload, dict):
        out = {}
        for key, value in payload.items():
            key_lower = str(key).lower()
            if key_lower in {"hostname", "fqdn"}:
                out[key] = _stable_token(str(value), key_lower)
            else:
                out[key] = redact_payload(value, mode)
        return out
    if isinstance(payload, list):
        return [redact_payload(item, mode) for item in payload]
    if isinstance(payload, str):
        return redact_text(payload, mode)
    return payload
