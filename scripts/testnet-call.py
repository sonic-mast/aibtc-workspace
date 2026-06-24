#!/usr/bin/env python3
"""
testnet-call.py — run a Stacks *testnet* contract interaction locally, using the
agent's existing wallet seed and ONLY native aibtc MCP tools. No AIBTC_MNEMONIC
env var, no remote run.

Why this exists
---------------
The persisted wallet record in ~/.aibtc is pinned to network=mainnet (cached
SP... address). The aibtc server signs testnet txs with that mainnet-version-byte
address, and the testnet node rejects it with `BadAddressVersionByte`. The fix is
NOT a separate mnemonic env var and NOT a remote run — the seed is already on disk
and recoverable locally with the wallet password. This helper boots an ephemeral
`NETWORK=testnet` aibtc-mcp-server, derives the ST... testnet wallet from the SAME
seed (wallet_export -> wallet_import network=testnet), runs the call on the testnet
chain, then restores the mainnet wallet as active and deletes the throwaway testnet
record. The ST... address is deterministic, so testnet faucet funding to it
persists on-chain across invocations even though the local record is ephemeral.

Modes
-----
  address -> derive + print the ST... testnet address (fund this from the faucet)
  read    -> call_read_only_function  (no wallet, no gas)
  write   -> call_contract            (signs + broadcasts; needs testnet STX for gas)

Examples
--------
  python3 scripts/testnet-call.py address

  python3 scripts/testnet-call.py read \
    --contract STBEMQQVSS3K3SQTF2NRZMF82JHMNTHQKQ2J7DW5.legion-gov \
    --fn get-proposal-status --args '[{"type":"uint","value":"6"}]'

  python3 scripts/testnet-call.py write \
    --contract STBEMQQVSS3K3SQTF2NRZMF82JHMNTHQKQ2J7DW5.legion-gov \
    --fn stake --args '[{"type":"uint","value":"1000"}]'

Output: one JSON line on stdout. The mnemonic and password are never printed.
"""
import argparse
import json
import os
import subprocess

AIBTC_HOME = os.path.expanduser("~/.aibtc")
# The keystore is encrypted with the LITERAL string "${AIBTC_WALLET_PASSWORD}"
# because MCP params do not shell-expand (see memory/feedback_wallet_unlock_literal.md).
# This is a placeholder string, not a real secret. Override only if the keystore is
# ever re-encrypted with a different value.
PASSWORD = os.environ.get("AIBTC_WALLET_PASSWORD_LITERAL", "${AIBTC_WALLET_PASSWORD}")
TESTNET_WALLET_NAME = "sonic-mast-testnet-ephemeral"


def mainnet_wallet_id():
    try:
        return json.load(open(os.path.join(AIBTC_HOME, "config.json")))["activeWalletId"]
    except Exception:
        return None


class Server:
    """Thin JSON-RPC wrapper around an aibtc-mcp-server subprocess on a given network."""

    def __init__(self, network):
        self.p = subprocess.Popen(
            ["aibtc-mcp-server"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env={**os.environ, "NETWORK": network}, text=True, bufsize=1,
        )
        self._id = 0
        self._rpc("initialize", {
            "protocolVersion": "2024-11-05", "capabilities": {},
            "clientInfo": {"name": "testnet-call", "version": "1.0"},
        })

    def _rpc(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        self.p.stdin.write(json.dumps(msg) + "\n")
        self.p.stdin.flush()
        # The server occasionally writes non-JSON log lines to stdout; skip them
        # and return the first parseable JSON-RPC reply (don't crash on a stray line).
        for _ in range(200):
            line = self.p.stdout.readline()
            if not line:
                return {"error": {"message": "subprocess closed stdout"}}
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except Exception:
                continue
        return {"error": {"message": "no JSON-RPC response"}}

    def call(self, name, args):
        r = self._rpc("tools/call", {"name": name, "arguments": args})
        if "error" in r:
            return {"_err": r["error"]}
        for c in (r.get("result") or {}).get("content", []):
            if c.get("type") == "text":
                try:
                    return json.loads(c.get("text", ""))
                except Exception:
                    return {"_raw": c.get("text", "")}
        return {}

    def close(self):
        try:
            self.p.stdin.close()
            self.p.wait(timeout=8)
        except Exception:
            self.p.terminate()


def parse_contract(s):
    if "." not in s:
        raise SystemExit(json.dumps({"ok": False, "error": "contract must be ADDRESS.NAME"}))
    addr, name = s.split(".", 1)
    return addr, name


def derive_testnet_wallet(srv, main_id):
    """Unlock the mainnet wallet, export its seed, and import an ephemeral testnet
    wallet from the SAME seed. Leaves the testnet wallet active + unlocked and
    returns (testnet_wallet_id, {"stx": ST..., "btc": tb1...}). Caller MUST call
    cleanup_testnet_wallet() in a finally block."""
    srv.call("wallet_unlock", {"password": PASSWORD, **({"walletId": main_id} if main_id else {})})
    # remove any stale ephemeral testnet record from a prior crashed run
    wl = srv.call("wallet_list", {})
    for w in (wl.get("wallets") or wl.get("availableWallets") or []):
        if w.get("name") == TESTNET_WALLET_NAME and w.get("id"):
            if main_id:
                srv.call("wallet_switch", {"walletId": main_id})
            srv.call("wallet_delete", {"walletId": w["id"], "password": PASSWORD, "confirm": "DELETE"})
    ex = srv.call("wallet_export", {
        "password": PASSWORD, "confirm": "I_UNDERSTAND_THE_RISKS",
        **({"walletId": main_id} if main_id else {}),
    })
    mnem = ex.get("mnemonic") or ex.get("phrase") or (ex.get("wallet") or {}).get("mnemonic")
    if not mnem:
        raise RuntimeError("could not export seed: %s" % ex.get("_err"))
    imp = srv.call("wallet_import", {
        "name": TESTNET_WALLET_NAME, "mnemonic": mnem,
        "password": PASSWORD, "network": "testnet",
    })
    # wallet_import returns the id under "walletId" and the ST... address under
    # "Stacks (L2)"."Address".
    tid = imp.get("walletId") or (imp.get("wallet") or {}).get("id")
    stx = (imp.get("Stacks (L2)") or {}).get("Address")
    if not tid:
        raise RuntimeError("wallet_import returned no walletId: %s" % json.dumps(imp)[:200])
    # Import does NOT auto-activate — explicitly switch + unlock the testnet wallet.
    srv.call("wallet_switch", {"walletId": tid})
    srv.call("wallet_unlock", {"password": PASSWORD, "walletId": tid})
    # SAFETY: never broadcast unless the active wallet is now the ST... testnet
    # address (guards against silently signing with the mainnet SP... record).
    st = srv.call("wallet_status", {})
    active = (st.get("wallet") or {}).get("address") or ""
    if not active.startswith("ST"):
        raise RuntimeError("testnet wallet did not activate (active=%s)" % active)
    return tid, {"stx": stx or active, "btc": (st.get("wallet") or {}).get("btcAddress")}


def cleanup_testnet_wallet(srv, main_id, tid):
    """ALWAYS restore the mainnet wallet as active and drop the throwaway testnet
    record, so the mainnet combined loop is never left pointed at the testnet wallet."""
    if main_id:
        srv.call("wallet_switch", {"walletId": main_id})
    if tid:
        srv.call("wallet_delete", {"walletId": tid, "password": PASSWORD, "confirm": "DELETE"})


def main():
    ap = argparse.ArgumentParser(description="Run a Stacks testnet contract call locally via native aibtc tools.")
    ap.add_argument("mode", choices=["address", "read", "write"])
    ap.add_argument("--contract", help="ADDRESS.NAME (read/write)")
    ap.add_argument("--fn", help="function name (read/write)")
    ap.add_argument("--args", default="[]", help="JSON array of Clarity function args")
    ap.add_argument("--sender", default=None, help="read-only sender ST... (default: contract address)")
    ap.add_argument("--pc-mode", default="deny", choices=["deny", "allow"], help="write post-condition mode")
    ap.add_argument("--pc", default="[]", help="JSON array of post-conditions (write)")
    a = ap.parse_args()

    out = {"ok": False, "mode": a.mode}
    srv = Server("testnet")
    try:
        if a.mode == "address":
            main_id = mainnet_wallet_id()
            tid = None
            try:
                tid, addrs = derive_testnet_wallet(srv, main_id)
                out["ok"] = bool(addrs.get("stx"))
                out["testnetAddress"] = addrs.get("stx")
                out["testnetBtcAddress"] = addrs.get("btc")
            finally:
                cleanup_testnet_wallet(srv, main_id, tid)
            print(json.dumps(out))
            return

        if not a.contract or not a.fn:
            out["error"] = "--contract and --fn are required for read/write"
            print(json.dumps(out))
            return
        addr, _cname = parse_contract(a.contract)
        fnargs = json.loads(a.args)
        out.update({"contract": a.contract, "fn": a.fn})

        if a.mode == "read":
            res = srv.call("call_read_only_function", {
                "contractId": a.contract,
                "functionName": a.fn, "functionArgs": fnargs,
                "senderAddress": a.sender or addr,
            })
            out["ok"] = "_err" not in res
            out["result"] = res
            print(json.dumps(out))
            return

        # write: derive the testnet wallet from the same seed (ephemeral, self-cleaning)
        main_id = mainnet_wallet_id()
        tid = None
        try:
            tid, addrs = derive_testnet_wallet(srv, main_id)
            out["testnetAddress"] = addrs.get("stx")
            res = srv.call("call_contract", {
                "contractAddress": addr, "contractName": _cname, "functionName": a.fn,
                "functionArgs": fnargs, "postConditionMode": a.pc_mode,
                "postConditions": json.loads(a.pc),
            })
            out["result"] = res
            out["txid"] = res.get("txid") or res.get("txId") or (res.get("transaction") or {}).get("txid")
            out["ok"] = bool(out["txid"]) and "_err" not in res
            if not out["ok"]:
                out["error"] = res.get("_err") or "no txid returned"
        finally:
            cleanup_testnet_wallet(srv, main_id, tid)
        print(json.dumps(out))
    finally:
        srv.close()


if __name__ == "__main__":
    main()
