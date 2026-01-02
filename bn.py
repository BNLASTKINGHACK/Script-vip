# bdg_bot_debug_plain_multi.py
# BN LAST KING – Multi-Channel Result Display (Clean Style)

import requests
import time
import random
import os
import sys
import json
from datetime import datetime

# ========== CONFIG ==========
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "8205778039:AAGhzXAh1LTn69RKkSCTy-Y1fOwpini0t9Y"

# ✅ Five Channel IDs (Add yours below)
TELEGRAM_CHAT_IDS = [
    os.getenv("TELEGRAM_CHAT_ID1") or "-1002706918839",
    os.getenv("TELEGRAM_CHAT_ID2") or "-1001412774395",
    os.getenv("TELEGRAM_CHAT_ID3") or "-1002196513628",
    os.getenv("TELEGRAM_CHAT_ID4") or "-1001880365150",
    os.getenv("TELEGRAM_CHAT_ID5") or ""
]

API_URL_TEMPLATE = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
POLL_INTERVAL_SECONDS = 6
MAX_HISTORY_KEEP = 200
CONSOLIDATED_SHOW = 20
DEBUG = True
DEBUG_LOGFILE = "debug.log"

WIN_STICKERS = [
    "CAACAgUAAxkBAAEB8qZpVoKeDy3ZVydlu3MaIy-7CzaWlwAC8xYAAnO8uFYNYR8Gn41GNTgE"
]

# ========== STATE ==========
history_data = []  # [{period,prediction,status,actual}]
last_fetched_period = None
loss_count = 0
pattern_mode = False
pattern_level = 0
current_pattern = []

# ========== UTIL ==========
def dlog(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    try:
        with open(DEBUG_LOGFILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except:
        pass

def send_telegram_message(text):
    for chat_id in TELEGRAM_CHAT_IDS:
        if not chat_id.strip():
            continue
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        params = {"chat_id": chat_id, "text": text}
        try:
            r = requests.get(url, params=params, timeout=12)
            dlog(f"[MSG] chat:{chat_id} status:{r.status_code}")
        except Exception as e:
            dlog(f"[MSG ERROR] chat:{chat_id} err:{e}")

def send_telegram_sticker(sticker_id):
    for chat_id in TELEGRAM_CHAT_IDS:
        if not chat_id.strip():
            continue
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendSticker"
        params = {"chat_id": chat_id, "sticker": sticker_id}
        try:
            requests.get(url, params=params, timeout=12)
        except Exception as e:
            dlog(f"[STICKER ERROR] chat:{chat_id} err:{e}")

def write_log(line):
    try:
        with open("results.txt", "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        dlog(f"write_log error: {e}")

def find_issues_in_response(obj):
    if isinstance(obj, dict):
        for k in ("list","data","rows","results","issues"):
            v = obj.get(k)
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return v
        for v in obj.values():
            found = find_issues_in_response(v)
            if found:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_issues_in_response(item)
            if found:
                return found
    return None

def fetch_game_history():
    try:
        ts = int(time.time() * 1000)
        url = API_URL_TEMPLATE.format(ts)
        r = requests.get(url, timeout=12)
        if r.status_code != 200:
            dlog(f"API HTTP {r.status_code} text:{r.text[:200]}")
            return []
        data = r.json()
        issues = find_issues_in_response(data) or []
        dlog(f"Fetched {len(issues)} issues from API")
        return issues
    except Exception as e:
        dlog(f"API fetch error: {e}")
        return []

def extract_period_and_number(item):
    if not isinstance(item, dict):
        return (None, None)
    period_keys = ["issueNumber","issue","period","issueNo","issue_number","issueno","issueNo"]
    number_keys = ["number","openNumber","openResult","result","openNum","open_num"]
    period = None
    number = None
    for k in period_keys:
        if k in item and item[k] not in (None, ""):
            period = str(item[k])
            break
    for k in number_keys:
        if k in item:
            try:
                number = int(item[k])
                break
            except:
                pass
    return (period, number)

def get_label(value):
    try:
        return "BIG" if int(value) >= 5 else "SMAL"
    except:
        return "UNKNOWN"

def start_pattern(base_value):
    global current_pattern
    if base_value == "SMAL":
        current_pattern = ["SMAL", "SMAL", "BIG", "BIG"]
    else:
        current_pattern = ["BIG", "BIG", "SMAL", "SMAL"]

def predict_next():
    global pattern_mode, pattern_level
    if pattern_mode and pattern_level < len(current_pattern):
        return current_pattern[pattern_level]
    elif history_data and history_data[-1].get("actual") is not None:
        return get_label(history_data[-1]["actual"])
    else:
        return random.choice(["BIG","SMAL"])

def build_plain_message():
    lines = []
    for it in history_data[-CONSOLIDATED_SHOW:]:
        p = it.get("period", "")
        pred = it.get("prediction", "")
        status = it.get("status", "Pending")
        if status == "WIN":
            lines.append(f"{p} {pred} WIN ✅")
        elif status == "LOSS":
            lines.append(f"{p} {pred} MISS")
        else:
            lines.append(f"{p} {pred} ⏳")
    return "\n".join(lines)

# ========== MAIN LOOP ==========
def main_loop():
    global last_fetched_period, loss_count, pattern_mode, pattern_level, history_data
    resolved_since_last_summary = 0

    while True:
        issues = fetch_game_history()
        if not issues:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        candidate = issues[0]
        p, n = extract_period_and_number(candidate)
        if not p or n is None:
            time.sleep(POLL_INTERVAL_SECONDS)
            continue

        if p != last_fetched_period:
            last_fetched_period = p
            actual_label = get_label(n)
            dlog(f"New Period: {p} | Number: {n} ({actual_label})")

            resolved = False
            for item in history_data:
                if item.get("period") == p and item.get("status") == "Pending":
                    if item.get("prediction") == actual_label:
                        item["status"] = "WIN"
                        send_telegram_sticker(random.choice(WIN_STICKERS))
                        loss_count = 0
                        pattern_mode = False
                        pattern_level = 0
                    else:
                        item["status"] = "LOSS"
                        loss_count += 1
                        if not pattern_mode:
                            base = history_data[-1]["prediction"] if history_data else item.get("prediction")
                            start_pattern(base)
                            pattern_mode = True
                            pattern_level = 0
                        else:
                            pattern_level = (pattern_level + 1) % len(current_pattern)
                    item["actual"] = n
                    write_log(f"{p} {item['prediction']} {item['status']}")
                    resolved = True
                    break

            if not resolved:
                for it in reversed(history_data):
                    if it.get("status") == "Pending":
                        if it.get("prediction") == actual_label:
                            it["status"] = "WIN"
                            send_telegram_sticker(random.choice(WIN_STICKERS))
                            loss_count = 0
                        else:
                            it["status"] = "LOSS"
                            loss_count += 1
                        it["actual"] = n
                        write_log(f"{it['period']} {it['prediction']} {it['status']}")
                        break

            try:
                next_p = str(int(p) + 1)
            except:
                next_p = p + "_n"

            pred = predict_next()
            history_data.append({"period": next_p, "prediction": pred, "status": "Pending", "actual": None})
            write_log(f"PREDICT | {next_p} {pred}")

            if len(history_data) > MAX_HISTORY_KEEP:
                history_data = history_data[-MAX_HISTORY_KEEP:]

            msg = build_plain_message()
            send_telegram_message(msg)

        time.sleep(POLL_INTERVAL_SECONDS)

# ========== RUN ==========
if __name__ == "__main__":
    if not TELEGRAM_BOT_TOKEN.strip():
        print("💔 TELEGRAM_BOT_TOKEN missing")
        sys.exit(1)
    print("✅ BN LAST KING BOT STARTED (Multi-Channel Plain Style)")
    try:
        main_loop()
    except KeyboardInterrupt:
        print("🛑 Stopped by user.")
    except Exception as e:
        print(f"⚠️ Fatal Error: {e}")