#!/usr/bin/env bash
# telegram-send.sh — ping the operator on Telegram from any shell, scheduled or interactive.
#
# Why this exists: the scheduled loop's Bash shell has STATE_API_TOKEN / GEMINI_API_KEY
# (settings.json env + ~/.zshenv) but NOT TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID — those
# live only in .env. A bare `curl .../bot$TELEGRAM_BOT_TOKEN/sendMessage` therefore hits
# `/bot/sendMessage` and Telegram answers 404 "Not Found" (every scheduled ping 2026-09-09
# through 2026-09-17 failed this way; only interactive sessions that `source .env` got through).
# This script resolves both vars from .env with a targeted grep|cut (never a wholesale
# `source .env` — see memory/state-api-reliability.md) and fails loudly on a non-ok reply.
#
# Usage:
#   scripts/telegram-send.sh "message text"     # send; prints Telegram's JSON, exit 1 on !ok
#   scripts/telegram-send.sh --check            # no send: verify token + chat resolve (getMe/getChat)
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${AIBTC_ENV_FILE:-$ROOT/.env}"
# Worktrees don't carry .env; fall back to the main checkout (parent of the shared .git dir).
if [ ! -f "$ENV_FILE" ] && [ -z "${AIBTC_ENV_FILE:-}" ]; then
  common="$(git -C "$ROOT" rev-parse --git-common-dir 2>/dev/null || true)"
  [ -n "$common" ] && [ -f "$(dirname "$common")/.env" ] && ENV_FILE="$(dirname "$common")/.env"
fi

_from_env_file() {  # $1 = var name; prints value (quotes stripped) or nothing
  [ -f "$ENV_FILE" ] || return 0
  grep -m1 "^\(export \)\?$1=" "$ENV_FILE" | cut -d= -f2- | sed -e 's/[[:space:]]*$//' -e 's/^["'"'"']//' -e 's/["'"'"']$//'
}

TOKEN="${TELEGRAM_BOT_TOKEN:-$(_from_env_file TELEGRAM_BOT_TOKEN)}"
CHAT="${TELEGRAM_CHAT_ID:-$(_from_env_file TELEGRAM_CHAT_ID)}"

if [ -z "$TOKEN" ] || [ -z "$CHAT" ]; then
  echo "telegram-send: TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID unset and not found in $ENV_FILE" >&2
  exit 2
fi

API="https://api.telegram.org/bot$TOKEN"

if [ "${1:-}" = "--check" ]; then
  me="$(curl -s --max-time 20 "$API/getMe")"
  chat="$(curl -s --max-time 20 "$API/getChat" -d "chat_id=$CHAT")"
  echo "getMe:   $(printf '%s' "$me"   | python3 -c 'import sys,json; d=json.load(sys.stdin); print("ok @"+d["result"]["username"] if d.get("ok") else "FAIL "+str(d))')"
  echo "getChat: $(printf '%s' "$chat" | python3 -c 'import sys,json; d=json.load(sys.stdin); print("ok "+d["result"].get("type","?") if d.get("ok") else "FAIL "+str(d))')"
  printf '%s' "$me" | grep -q '"ok":true' && printf '%s' "$chat" | grep -q '"ok":true'
  exit $?
fi

TEXT="${1:?usage: telegram-send.sh \"message\" | --check}"
resp="$(curl -s --max-time 30 "$API/sendMessage" -d "chat_id=$CHAT" --data-urlencode "text=$TEXT")"
# Never echo the token: Telegram error bodies don't include it, but keep the URL out of output.
echo "$resp"
printf '%s' "$resp" | grep -q '"ok":true'
