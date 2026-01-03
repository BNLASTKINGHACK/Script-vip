#!/usr/bin/env python3
import os, sys, time, subprocess, importlib, random

# ==================================================
# 🔰 Auto Install & Import Packages (Fixed for PyDroid)
# ==================================================
def install_and_import(package, pip_name=None):
    pip_name = pip_name or package
    try:
        return importlib.import_module(package)
    except ImportError:
        print(f"📦 Installing missing package: {pip_name} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pip_name])
        return importlib.import_module(package)

# ✅ Correct modules for PyDroid
requests = install_and_import("requests")
colorama = install_and_import("colorama")
cfonts = install_and_import("cfonts", "cfonts")

from colorama import Fore, Style
from cfonts import render

# ==================================================
# ⚙️ Settings
# ==================================================
API_URL = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10)",
    "Referer": "https://hgnice.biz"
}

# ==================================================
# 🎨 Colors
# ==================================================
YELLOW = Fore.YELLOW
GREEN = Fore.GREEN
RESET = Style.RESET_ALL
BOLD = Style.BRIGHT

# ==================================================
# 🧠 Typewriter Effect
# ==================================================
def type_writer(text, delay=0.0009):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

# ==================================================
# 💀 DIABLO SCRIPT Banner
# ==================================================
def banner():
    output = render(
        'DIABLO SCRIPT',
        colors=['yellow', 'green'],
        align='center',
        font='block'
    )
    for line in output.split("\n"):
        type_writer(line)
    type_writer(f"{GREEN}💀🔥 WELCOME TO DIABLO SCRIPT SYSTEM 🔥💀{RESET}\n", 0.002)
    type_writer(f"{YELLOW}⚔️  Powered by BN LAST KING ⚔️{RESET}\n", 0.002)
    print(GREEN + "=" * 70 + RESET + "\n")

# ==================================================
# 📊 Prediction Logic
# ==================================================
def get_big_small(num):
    try:
        return "BIG" if int(num) >= 5 else "SMALL"
    except:
        return "Unknown"

def fetch_data():
    try:
        ts = int(time.time() * 1000)
        url = API_URL.format(ts)
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        result = response.json()
        if 'data' in result and 'list' in result['data']:
            formatted = []
            for item in result['data']['list']:
                formatted.append({
                    "issueNumber": item.get("issueNumber"),
                    "number": item.get("number")
                })
            return formatted
        else:
            raise ValueError("Invalid API structure")
    except Exception as e:
        print(f"{YELLOW}⚠️ Error fetching data: {e}{RESET}")
        return []

def stable_prediction(period_number, last_results, prev_prediction=None):
    recent = last_results[-10:]
    labeled = ["BIG" if int(r) >= 5 else "SMALL" for r in recent]

    big_count = labeled.count("BIG")
    small_count = labeled.count("SMALL")

    if big_count > small_count:
        history_pred = "BIG"
    elif small_count > big_count:
        history_pred = "SMALL"
    else:
        history_pred = "BIG" if int(period_number[-1]) >= 5 else "SMALL"

    last3 = int(period_number[-3:]) if period_number.isdigit() else 0
    digit_sum = sum(int(d) for d in str(last3))
    period_pred = "BIG" if digit_sum % 2 == 0 else "SMALL"

    if history_pred == period_pred:
        base_pred = "SMALL" if history_pred == "BIG" else "BIG"
    else:
        base_pred = history_pred

    if prev_prediction and base_pred == prev_prediction:
        base_pred = "SMALL" if base_pred == "BIG" else "BIG"

    if random.random() < 0.25:
        final_pred = "SMALL" if base_pred == "BIG" else "BIG"
    else:
        final_pred = base_pred

    return final_pred

# ==================================================
# 🧾 Display Helpers
# ==================================================
def print_prediction(period, prediction):
    print(f"{GREEN}⚔️  Period ➞ {YELLOW}{period}{RESET}")
    print(f"{GREEN}🔮  Prediction ➞ {YELLOW}{prediction}{RESET}")
    sys.stdout.write(f"{GREEN}🎯  Result ➞ {RESET}")
    sys.stdout.flush()

def print_result(win):
    if win:
        sys.stdout.write(GREEN + BOLD + "✅ VICTORY!\n\n" + RESET)
    else:
        sys.stdout.write(YELLOW + BOLD + "❌ DEFEAT!\n\n" + RESET)
    sys.stdout.flush()

# ==================================================
# 🔁 Main Loop
# ==================================================
def run_console():
    seen_periods = set()
    prediction = None
    last_results = []
    prev_prediction = None

    banner()

    while True:
        data = fetch_data()
        if not data:
            time.sleep(2)
            continue

        latest = data[0]
        current_period = latest.get("issueNumber", "")
        result_number = latest.get("number", "")

        try:
            last_results.append(int(result_number))
            if len(last_results) > 50:
                last_results.pop(0)
        except ValueError:
            pass

        if prediction and prediction["period"] == current_period:
            win = prediction["prediction"] == get_big_small(result_number)
            print_result(win)
            prev_prediction = prediction["prediction"]
            prediction = None

        if not prediction and current_period not in seen_periods:
            seen_periods.add(current_period)
            next_period = str(int(current_period) + 1) if current_period.isdigit() else ""
            next_prediction = stable_prediction(current_period, last_results, prev_prediction)
            prediction = {"period": next_period, "prediction": next_prediction}

            show_period = next_period[-5:] if len(next_period) >= 5 else next_period
            print_prediction(show_period, next_prediction)

        time.sleep(3)

# ==================================================
# 🚀 Run Script
# ==================================================
if __name__ == "__main__":
    run_console()