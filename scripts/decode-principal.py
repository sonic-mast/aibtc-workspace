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
    # c32check keeps exactly one "0" symbol per leading zero BYTE and no other
    # padding. Padding to a fixed ceil(len*8/5) width instead looks right for
    # most inputs but prepends a spurious "0" whenever the encoded integer is
    # short — ~19% of real addresses, which are 40 chars rather than 41.
    pad = 0
    for b in data:
        if b:
            break
        pad += 1
    return "0" * pad + out


def c32check(version: int, hash160: bytes) -> str:
    checksum = hashlib.sha256(hashlib.sha256(bytes([version]) + hash160).digest()).digest()[:4]
    return "S" + C32[version] + c32encode(hash160 + checksum)


def decode(hexstr: str) -> str:
    raw = bytes.fromhex(hexstr.strip().removeprefix("0x"))
    # unwrap (ok …) and (some …); an (err …) is a real contract failure and
    # must surface rather than be peeled open to whatever it wraps
    if raw[:1] == b"\x08":
        raise ValueError("contract returned (err …), not a principal")
    while raw[:1] in (b"\x07", b"\x0a"):
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


# Vectors are real on-chain values, never hand-built (appending an invented
# contract name to a real address is exactly the fabrication REVIEW.md check 1
# forbids). The first three encode to 40-char addresses — the short case a
# fixed-width pad silently corrupts, which is what made this decoder wrong.
SELFTEST = [
    ("0x051625e7097721a3a3f32a2af0ae3c59682253389f1a", "SPJYE2BQ46HT7WSA5BRAWF2SD0H56E4Z3BJ103P9"),
    ("0x051602e646242d96074700956359f26018b7a70dd92c", "SP1ECHH45PB0EHR0JNHNKWK032VTE3ES5HWCN85D"),
    (
        "0x0616211fc91180711cd91676d2d9a4c5940694c654b30a6d656d62657273686970",
        "SPGHZJ8HG1RHSP8PEV9DK965JG399HJMPCAVKKNX.membership",
    ),
    (
        "0x061ab750c0ce5f6d4a2a53667c18e0a0f5d9b7e666440a736274632d746f6b656e",
        "ST2VN1G6EBXPMMAJKCSY1HR50YQCVFSK68KKP9SKW.sbtc-token",
    ),
]


def selftest() -> int:
    failed = 0
    for hexstr, expected in SELFTEST:
        try:
            got = decode(hexstr)
        except ValueError as exc:
            got = f"<{exc}>"
        if got != expected:
            failed += 1
            print(f"FAIL {hexstr[:24]}…\n  want {expected}\n  got  {got}", file=sys.stderr)
    print(f"selftest: {len(SELFTEST) - failed}/{len(SELFTEST)} passed")
    return 1 if failed else 0


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else sys.stdin.read()
    arg = arg.strip()
    if arg == "--selftest":
        return selftest()
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
