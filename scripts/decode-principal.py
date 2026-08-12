#!/usr/bin/env python3
"""Decode a Clarity principal from a call-read hex result to `ST….name` form.

`testnet-call.py read` returns raw Clarity hex. Reads that answer "which
contract is actually wired here" (the Legion treasury's `get-token`, most
importantly) are therefore unusable without this step, which is how the loop
ended up carrying a hardcoded sBTC token that no longer exists on-chain.

Handles the two principal encodings and unwraps a single (ok ...) response:
  0x05 <ver:1> <hash160:20>                      -> standard principal
  0x06 <ver:1> <hash160:20> <len:1> <name>       -> contract principal

Usage:
  scripts/decode-principal.py 0x061ab750...6e   # -> ST2VN…KKP9SKW.sbtc-token
  testnet-call.py read ... | jq -r .result.result | scripts/decode-principal.py
"""
import hashlib
import json
import sys

C32 = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def c32encode(data: bytes) -> str:
    n = int.from_bytes(data, "big")
    out = ""
    while n:
        out = C32[n & 31] + out
        n >>= 5
    # 5 bits per symbol, rounded up, so leading zero bytes keep their place
    return out.rjust(-(-len(data) * 8 // 5), "0")


def c32check(version: int, hash160: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(bytes([version]) + hash160).digest()).digest()[:4]
    return "S" + C32[version] + c32encode(hash160 + checksum)


def decode(hexstr: str) -> str:
    raw = bytes.fromhex(hexstr.strip().removeprefix("0x"))
    # unwrap (ok <principal>) — 0x07 is the response-ok wrapper
    if raw[:1] == b"\x07":
        raw = raw[1:]
    kind = raw[0]
    if kind not in (0x05, 0x06):
        raise ValueError(f"not a principal (leading byte 0x{kind:02x})")
    version, hash160 = raw[1], raw[2:22]
    address = c32check(version, hash160)
    if kind == 0x05:
        return address
    name_len = raw[22]
    name = raw[23 : 23 + name_len].decode("ascii")
    if len(name) != name_len:
        raise ValueError("truncated contract name")
    return f"{address}.{name}"


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    arg = arg.strip()
    # accept a full testnet-call.py envelope as well as a bare hex string
    if arg.startswith("{"):
        payload = json.loads(arg)
        arg = payload.get("result", {}).get("result", "")
    if not arg:
        print("usage: decode-principal.py <0x-hex>  (or pipe it on stdin)", file=sys.stderr)
        return 2
    try:
        print(decode(arg))
    except (ValueError, IndexError, UnicodeDecodeError) as exc:
        print(f"decode failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
