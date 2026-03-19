import os
import re
import sys
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

RAW_FOLDER = BASE_DIR / "Raw Files"
FINAL_FOLDER = BASE_DIR / "Final Files"
SUMMARY_FOLDER = BASE_DIR / "Summary"

os.makedirs(FINAL_FOLDER, exist_ok=True)
os.makedirs(SUMMARY_FOLDER, exist_ok=True)

ICON_TITLE = "\U0001F4CA"
ICON_SECTION = "\U0001F7E1"
ICON_LIST = "\U0001F7E2"
ICON_PROMPT = "\U0001F539"
ICON_FOLDER = "\U0001F4C2"
UI_LINE = "\u2500" * 40
LABEL_WIDTH = 12
PAIR_LABEL_WIDTH = 6
PROMPT_LABEL_WIDTH = 12
SETUP_PROMPT_LABEL_WIDTH = 34
TRADE_REVIEW_LEFT_WIDTH = 26
TRADE_REVIEW_RIGHT_WIDTH = 26
TRADE_REVIEW_SPLIT_WIDTH = 18
TRADE_REVIEW_TOTAL_WIDTH = 46

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*m")

ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_UNDERLINE = "\033[4m"
ANSI_GREEN = "\033[92m"
ANSI_RED = "\033[91m"
ANSI_YELLOW = "\033[93m"
ANSI_CYAN = "\033[96m"


def _stdout_supports(text: str) -> bool:
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(encoding)
        return True
    except Exception:
        return False


if not all(
    _stdout_supports(token)
    for token in [ICON_TITLE, ICON_SECTION, ICON_LIST, ICON_PROMPT, ICON_FOLDER, UI_LINE]
):
    ICON_TITLE = "[TRADE]"
    ICON_SECTION = "*"
    ICON_LIST = "-"
    ICON_PROMPT = ">"
    ICON_FOLDER = "[DIR]"
    UI_LINE = "-" * 40

CURRENCY_SYMBOL = "\u20B9" if _stdout_supports("\u20B9") else "Rs."

SUMMARY_COLUMNS = [
    "Trade",
    "Entry Date",
    "Entry Time",
    "Entry Price",
    "Exit Date",
    "Exit Time",
    "Exit Price",
    "Qty",
    "PL Points",
    "PL Amt",
    "Max MTM Date",
    "Max MTM Time",
    "Max MTM Price",
    "Max MTM Amt",
]

PIVOT_LOOKBACK = 3
EMA_BODY_SIDE_RATIO_MIN = 0.30
DATE_OUTPUT_FORMAT = "%d-%b-%y"
TIME_OUTPUT_FORMAT = "%H.%M"
FIRST_CANDLE_TIME = "09.15"


def clear():
    os.system("cls" if os.name == "nt" else "clear")


def header(title: str):
    clear()
    print(f"{ICON_TITLE} EMA TRADE MANAGER")
    print(UI_LINE)
    print()
    print(f"{ANSI_BOLD}{ANSI_CYAN}{ICON_SECTION} {title}{ANSI_RESET}")
    print()


def print_line():
    print(UI_LINE)


def print_menu_option(text: str):
    print(f"{ICON_LIST} {text}")


def print_dual_menu_options(left_text: str, right_text: str, gap: int = 12):
    print(f"{ICON_LIST} {left_text}" + (" " * gap) + f"{ICON_LIST} {right_text}")


def print_section(title: str):
    print(f"{ANSI_BOLD}{ANSI_CYAN}{ICON_SECTION} {title}{ANSI_RESET}")


def print_kv(label: str, value):
    print(f"{label:<{LABEL_WIDTH}}: {value}")


def print_kv_pair(label1: str, value1, label2: str, value2):
    print(f"{label1:<{LABEL_WIDTH}}: {value1}     {label2:<{PAIR_LABEL_WIDTH}}: {value2}")


def prompt_input(label: str, inline=False, label_width=None, leading_blank=True) -> str:
    if not inline:
        if leading_blank:
            print()
        print_line()
    width = len(label) if label_width is None else label_width
    return input(f"{ICON_PROMPT} {label:<{width}} : ").strip()


def extract_symbol(file_name: str) -> str:
    name = file_name.replace(".csv", "")
    name = name.replace("NSE_", "")
    name = re.sub(r",.*", "", name)
    return name.capitalize()


def list_raw_symbols():
    symbol_files = {}
    for f in os.listdir(RAW_FOLDER):
        if not f.lower().endswith(".csv"):
            continue
        sym = extract_symbol(f)
        symbol_files.setdefault(sym, []).append(os.path.join(RAW_FOLDER, f))
    return symbol_files


def normalize_date(x: str) -> str:
    dt = pd.to_datetime(x, dayfirst=True)
    return dt.strftime(DATE_OUTPUT_FORMAT)


def normalize_time(x: str) -> str:
    x = x.strip().replace(":", ".")
    parts = x.split(".")
    if len(parts) != 2:
        raise ValueError("Invalid time format")
    hour = int(parts[0])
    minute = int(parts[1])
    return f"{hour:02d}.{minute:02d}"


def format_output_date(value) -> str:
    if pd.isna(value):
        return ""

    dt = pd.to_datetime(value, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return str(value).strip()
    return dt.strftime(DATE_OUTPUT_FORMAT)


def format_output_time(value) -> str:
    if pd.isna(value):
        return ""

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        numeric = float(value)
        if 0 <= numeric < 1:
            total_minutes = int(round(numeric * 24 * 60))
            hour = (total_minutes // 60) % 24
            minute = total_minutes % 60
            return f"{hour:02d}.{minute:02d}"

    text = str(value).strip()
    if not text:
        return ""

    match = re.fullmatch(r"(\d{1,2})[:.](\d{1,2})(?:[:.](\d{1,2}))?", text)
    if match:
        hour = int(match.group(1))
        minute_text = match.group(2)
        minute = int(minute_text)

        # Older sheets sometimes store 9.3 for 09.30 after Excel trimming the zero.
        if len(minute_text) == 1:
            minute *= 10

        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return f"{hour:02d}.{minute:02d}"

    dt = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(dt):
        return text
    return dt.strftime(TIME_OUTPUT_FORMAT)


def is_first_candle_time(value) -> bool:
    return format_output_time(value) == FIRST_CANDLE_TIME


def normalize_output_sheet(df):
    out = df.copy()
    for col in out.columns:
        if "Date" in col:
            out[col] = out[col].apply(format_output_date)
        elif "Time" in col:
            out[col] = out[col].apply(format_output_time)
    return out


def normalize_cached_time_series(series):
    text = series.astype(str).str.strip().str.replace(":", ".", regex=False)
    parts = text.str.extract(r"^(\d{1,2})(?:\.(\d{1,2}))?$")

    hour = pd.to_numeric(parts[0], errors="coerce")
    minute = pd.to_numeric(parts[1], errors="coerce")
    minute = minute.fillna(0)
    one_digit_minute = parts[1].str.len() == 1
    minute = minute.where(~one_digit_minute, minute * 10)

    valid = hour.between(0, 23) & minute.between(0, 59)
    out = text.copy()
    out.loc[valid] = (
        hour.loc[valid].astype(int).astype(str).str.zfill(2)
        + "."
        + minute.loc[valid].astype(int).astype(str).str.zfill(2)
    )
    return out


def describe_missing_candle(df, date, time):
    day_rows = df[df["Date"] == date].copy()
    if day_rows.empty:
        return f"No candle found for {date}. That date is not available in the current dataset."

    day_rows["TimeNorm"] = day_rows["Time"].apply(format_output_time)
    times = day_rows["TimeNorm"].dropna().drop_duplicates().sort_values().reset_index(drop=True)
    if times.empty:
        return f"No candle found for {date} {time}."

    target = pd.to_datetime(time, format=TIME_OUTPUT_FORMAT, errors="coerce")
    parsed_times = pd.to_datetime(times, format=TIME_OUTPUT_FORMAT, errors="coerce")

    prev_times = times[parsed_times < target] if not pd.isna(target) else pd.Series(dtype="object")
    next_times = times[parsed_times > target] if not pd.isna(target) else pd.Series(dtype="object")

    prev_time = prev_times.iloc[-1] if not prev_times.empty else None
    next_time = next_times.iloc[0] if not next_times.empty else None

    if prev_time and next_time:
        return (
            f"No candle found for {date} {time}. "
            f"This dataset uses 3-minute candles; nearby times are {prev_time} and {next_time}."
        )
    if prev_time:
        return f"No candle found for {date} {time}. The last available candle on that date is {prev_time}."
    if next_time:
        return f"No candle found for {date} {time}. The first available candle on that date is {next_time}."
    return f"No candle found for {date} {time}."


def clean_symbol(files):
    dfs = [pd.read_csv(f) for f in files]
    df = pd.concat(dfs, ignore_index=True)

    if "time" not in df.columns:
        raise ValueError("Column 'time' not found in selected CSV")

    df["time"] = pd.to_datetime(df["time"], errors="coerce")
    df = df.dropna(subset=["time"]).sort_values("time")

    rename_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close",
        "ema": "EMA",
        "Open": "Open",
        "High": "High",
        "Low": "Low",
        "Close": "Close",
        "EMA": "EMA",
    }
    df = df.rename(columns=rename_map)

    required = ["Open", "High", "Low", "Close", "EMA"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(missing)}")

    df = df[df["EMA"].notna()]
    df = df[df["EMA"] != 0]

    df["Date"] = df["time"].dt.strftime(DATE_OUTPUT_FORMAT)
    df["Time"] = df["time"].dt.strftime(TIME_OUTPUT_FORMAT)
    df = df.drop_duplicates(subset=["Date", "Time"])

    out = df[["Date", "Time", "Open", "High", "Low", "Close", "EMA"]].copy()
    out["DateObj"] = pd.to_datetime(out["Date"], format="%d-%b-%y")
    return out.reset_index(drop=True)


def should_refresh_clean_file(source_files, output_path) -> bool:
    output = Path(output_path)
    if not output.exists():
        return True

    try:
        output_mtime = output.stat().st_mtime
        return any(Path(src).stat().st_mtime > output_mtime for src in source_files)
    except OSError:
        return True


def load_cached_clean_symbol(source_files, output_path):
    if should_refresh_clean_file(source_files, output_path):
        df_clean = clean_symbol(source_files)
        df_clean.drop(columns=["DateObj"], errors="ignore").to_csv(output_path, index=False)

    df = pd.read_csv(
        output_path,
        dtype={
            "Date": "string",
            "Time": "string",
        },
    )
    required = ["Date", "Time", "Open", "High", "Low", "Close", "EMA"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in cleaned file: {', '.join(missing)}")

    df["Date"] = df["Date"].astype(str).str.strip()
    df["Time"] = normalize_cached_time_series(df["Time"])
    df["DateObj"] = pd.to_datetime(df["Date"], format="%d-%b-%y")
    return df.reset_index(drop=True)

def sort_summary_file(scrip):

    path = SUMMARY_FOLDER / f"{scrip}.xlsx"

    if not path.exists():
        return

    try:
        df = pd.read_excel(path)
    except Exception:
        return

    if df.empty:
        return

    df = normalize_output_sheet(df)
    df.columns = df.columns.str.strip()

    required = ["Entry Date","Entry Time","Exit Date","Exit Time"]

    for col in required:
        if col not in df.columns:
            return

    # ---- REMOVE DUPLICATES FIRST ----
    df = df.drop_duplicates(
        subset=["Entry Date","Entry Time","Exit Date","Exit Time"]
    )

    # ---- DATE/TIME SORT KEY ----
    df["_date"] = pd.to_datetime(df["Entry Date"], format=DATE_OUTPUT_FORMAT, errors="coerce")
    df["_time"] = pd.to_datetime(df["Entry Time"], format=TIME_OUTPUT_FORMAT, errors="coerce")

    # ---- SORT ----
    df = df.sort_values(
        by=["_date","_time"],
        ascending=[True, True]
    )

    # remove helper columns
    df = df.drop(columns=["_date","_time"])

    df.to_excel(path, index=False)


def show_existing_trades_summary(scrip):

    path = SUMMARY_FOLDER / f"{scrip}.xlsx"

    print_kv(f"{ANSI_BOLD}{ANSI_CYAN}Existing Trades", "")

    if not path.exists():
        print("NO EXISTING TRADES")
        return None

    try:
        df = pd.read_excel(path)
    except Exception:
        print("NO EXISTING TRADES")
        return None

    if df.empty:
        print("NO EXISTING TRADES")
        return None

    df = normalize_output_sheet(df)
    df.columns = df.columns.str.strip()

    required = ["Entry Date","Entry Time","Exit Date","Exit Time"]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")

    # remove duplicate trades
    df = df.drop_duplicates(subset=required)

    # ---- SORTING ----

    df["_date_sort"] = pd.to_datetime(df["Entry Date"], format=DATE_OUTPUT_FORMAT, errors="coerce")
    df["_time_sort"] = pd.to_datetime(df["Entry Time"], format=TIME_OUTPUT_FORMAT, errors="coerce")

    df = df.sort_values(by=["_date_sort","_time_sort"]).reset_index(drop=True)

    df = df.drop(columns=["_date_sort","_time_sort"])

    # ---- CONTINUITY DETECTION ----

    blocks = []

    start_date = df.loc[0, "Entry Date"]
    start_time = df.loc[0, "Entry Time"]

    prev_exit_date = df.loc[0, "Exit Date"]
    prev_exit_time = df.loc[0, "Exit Time"]

    for i in range(1, len(df)):

        cur_entry_date = df.loc[i, "Entry Date"]
        cur_entry_time = df.loc[i, "Entry Time"]

        cur_exit_date = df.loc[i, "Exit Date"]
        cur_exit_time = df.loc[i, "Exit Time"]

        if cur_entry_date == prev_exit_date and cur_entry_time == prev_exit_time:

            prev_exit_date = cur_exit_date
            prev_exit_time = cur_exit_time

        else:

            blocks.append((start_date,start_time,prev_exit_date,prev_exit_time))

            start_date = cur_entry_date
            start_time = cur_entry_time

            prev_exit_date = cur_exit_date
            prev_exit_time = cur_exit_time

    blocks.append((start_date,start_time,prev_exit_date,prev_exit_time))

    # ---- PRINT OUTPUT ----

    for start_d,start_t,end_d,end_t in blocks:

        start_fmt = format_output_date(start_d)
        end_fmt = format_output_date(end_d)

        print_kv_pair(
            "From",
            f"{start_fmt} {start_t}",
            "To",
            f"{end_fmt} {end_t}"
        )

    suggested_start = format_output_date(prev_exit_date)

    print()
    print_kv("Suggested Start", f"{ANSI_BOLD}{ANSI_YELLOW}{suggested_start}{ANSI_RESET}")

    return suggested_start




def choose_scrip_and_load():
    header("Select Scrip")
    symbol_files = list_raw_symbols()
    if not symbol_files:
        print("No CSV files found in raw folder.")
        input(f"\n{ICON_PROMPT} Press Enter to exit...")
        return None, None

    symbols = sorted(symbol_files.keys(), key=str.lower)
    print(f"{ICON_FOLDER} Available Scrips\n")
    for i, s in enumerate(symbols, 1):
        print_menu_option(f"{i:02d} {s}")

    while True:
        try:
            choice = int(prompt_input("Enter Scrip Number"))
            if 1 <= choice <= len(symbols):
                break
        except Exception:
            pass
        print("Invalid selection. Enter a valid serial number.")

    scrip = symbols[choice - 1]
    source_files = symbol_files[scrip]
    final_path = os.path.join(FINAL_FOLDER, f"{scrip}.csv")
    df = load_cached_clean_symbol(source_files, final_path)

    header("Cleaned Dataset Summary")
    print_kv(f"{ANSI_BOLD}{ANSI_CYAN}Scrip", f"{scrip.upper()}{ANSI_RESET}")
    print_kv_pair(
        f"{ANSI_BOLD}{ANSI_CYAN}From Date",
        df["Date"].iloc[0],
        "To Date",
        f"{df['Date'].iloc[-1]}{ANSI_RESET}",
    )
    suggested_start = show_existing_trades_summary(scrip)
    print()
    return scrip, df, suggested_start


def get_default_qty(scrip, start_date):

    path = SUMMARY_FOLDER / f"{scrip}.xlsx"

    if not path.exists():
        return None

    try:
        df = pd.read_excel(path)
    except Exception:
        return None

    if df.empty:
        return None

    df = normalize_output_sheet(df)
    df.columns = df.columns.str.strip()

    if "Qty" not in df.columns:
        return None

    if "Exit Date" not in df.columns:
        return None

    try:
        df["_exit"] = pd.to_datetime(df["Exit Date"], format=DATE_OUTPUT_FORMAT, errors="coerce")
    except Exception:
        return None

    start_dt = pd.to_datetime(start_date, format=DATE_OUTPUT_FORMAT, errors="coerce")

    df = df[df["_exit"] <= start_dt]

    if df.empty:
        return None

    latest_row = df.sort_values("_exit").iloc[-1]

    try:
        qty = int(latest_row["Qty"])
        return qty if qty > 0 else None
    except Exception:
        return None

def ask_start_and_qty(df, scrip, suggested_start=None):

    while True:
        try:
            start_label = f"Enter Start Date (Default {suggested_start})" if suggested_start else "Enter Start Date"
            prompt_width = max(len(start_label), SETUP_PROMPT_LABEL_WIDTH)
            print()
            print_line()

            if suggested_start:
                start_input = prompt_input(start_label, inline=True, label_width=prompt_width)
                start = normalize_date(start_input) if start_input else suggested_start
            else:
                start = normalize_date(prompt_input(start_label, inline=True, label_width=prompt_width))

            default_qty = get_default_qty(scrip, start)
            qty_label = f"Enter Quantity (Default {default_qty})" if default_qty else "Enter Quantity"

            if default_qty:
                qty_input = prompt_input(qty_label, inline=True, label_width=prompt_width)
                qty = int(qty_input) if qty_input else default_qty
            else:
                qty = int(prompt_input(qty_label, inline=True, label_width=prompt_width))

            if qty <= 0:
                raise ValueError("Quantity must be positive")

            start_dt = pd.to_datetime(start, dayfirst=True)

            print()
            print_section("Confirm Inputs")
            print_kv("Start Date", start)
            print_kv("Quantity", qty)
            print()
            print_dual_menu_options("1 Accept", "2 Re-Enter")
            confirm = prompt_input("Select Option")
            if confirm == "1":
                break
            if confirm == "2":
                continue
            print("Invalid option.")
            continue

        except Exception as e:
            print(f"Invalid input: {e}")

    filtered = df[df["DateObj"] >= start_dt].reset_index(drop=True)

    if filtered.empty:
        raise ValueError("No records found on/after selected start date")

    return filtered, start, qty
def ask_trade_type(prompt):
    while True:
        print_section(prompt)
        print_menu_option("1 Buy")
        print_menu_option("2 Sell")
        ch = prompt_input("Select Option")
        if ch == "1":
            return "BUY"
        if ch == "2":
            return "SELL"
        print("Invalid option.")


def ask_entry_mode():
    while True:
        print()
        print_section("Entry Mode")
        print(UI_LINE)
        print_menu_option("1 - Auto Detection")
        print_menu_option("2 - Manual Entry")
        print(UI_LINE)
        ch = prompt_input("Select Option")
        if ch == "1":
            return "AUTO"
        if ch == "2":
            return "MANUAL"
        print("Invalid option.")


def find_row_index(df, min_index=0):
    while True:
        try:
            d = normalize_date(prompt_input("Entry Date (dd-mm-yyyy or dd-mmm-yy)"))
            t = normalize_time(prompt_input("Entry Time (HH:MM or HH.MM)"))
            mask = (df.index >= min_index) & (df["Date"] == d) & (df["Time"] == t)
            matches = df[mask]
            if matches.empty:
                any_match = df[(df["Date"] == d) & (df["Time"] == t)]
                if any_match.empty:
                    print("No matching candle found for this date/time in current dataset.")
                else:
                    print("Candle exists, but it is before the current allowed position.")
                continue
            return int(matches.index[0])
        except Exception as e:
            print(f"Invalid entry: {e}")


def ask_entry_price(row_close):
    return float(row_close)


def good_candle(row):
    body = abs(float(row["Close"]) - float(row["Open"]))
    rng = float(row["High"]) - float(row["Low"])
    if rng <= 0:
        return False

    body_ratio = body / rng
    upper = float(row["High"]) - max(float(row["Open"]), float(row["Close"]))
    lower = min(float(row["Open"]), float(row["Close"])) - float(row["Low"])
    upper_ratio = upper / rng
    lower_ratio = lower / rng

    is_doji = body_ratio <= 0.20
    is_wick = body_ratio <= 0.35 and (upper_ratio >= 0.50 or lower_ratio >= 0.50)
    indecision = body_ratio < 0.35 and upper_ratio > 0.30 and lower_ratio > 0.30
    return not (is_doji or is_wick or indecision)


def ensure_ema(df):
    if "EMA" not in df.columns:
        df["EMA"] = df["Close"].ewm(span=200, adjust=False).mean()
    return df


def ensure_pivot_swings(df, lookback=PIVOT_LOOKBACK):
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    n = len(df)

    pivot_high = [float("nan")] * n
    pivot_low = [float("nan")] * n

    for i in range(lookback, n - lookback):
        left = i - lookback
        right = i + lookback
        h_win = high.iloc[left: right + 1]
        l_win = low.iloc[left: right + 1]
        h = float(high.iloc[i])
        l = float(low.iloc[i])

        if h == float(h_win.max()) and int((h_win == h).sum()) == 1:
            pivot_high[i] = h
        if l == float(l_win.min()) and int((l_win == l).sum()) == 1:
            pivot_low[i] = l

    out = df.copy()
    out["PivotHigh3"] = pivot_high
    out["PivotLow3"] = pivot_low
    return out


def prepare_detection_frame(df, lookback=PIVOT_LOOKBACK):
    required_cols = ["PivotHigh3", "PivotLow3", "ConfirmedPivotHigh3", "ConfirmedPivotLow3"]
    if all(col in df.columns for col in required_cols):
        return df

    out = ensure_pivot_swings(ensure_ema(df.copy()), lookback=lookback)
    out["PivotHigh3"] = pd.to_numeric(out["PivotHigh3"], errors="coerce")
    out["PivotLow3"] = pd.to_numeric(out["PivotLow3"], errors="coerce")
    out["ConfirmedPivotHigh3"] = out["PivotHigh3"].shift(lookback).ffill()
    out["ConfirmedPivotLow3"] = out["PivotLow3"].shift(lookback).ffill()
    return out


def body_is_30pct_on_side_of_ema(row, side):
    open_ = float(row["Open"])
    close = float(row["Close"])
    ema = float(row["EMA"])
    body = abs(close - open_)
    if body <= 0:
        return False

    body_top = max(open_, close)
    body_bottom = min(open_, close)
    body_above_ema = max(0.0, body_top - max(body_bottom, ema))
    body_below_ema = max(0.0, min(body_top, ema) - body_bottom)

    if side == "BUY":
        return (body_above_ema / body) >= EMA_BODY_SIDE_RATIO_MIN
    if side == "SELL":
        return (body_below_ema / body) >= EMA_BODY_SIDE_RATIO_MIN
    return False


def get_latest_confirmed_swing(df, idx, side, lookback=PIVOT_LOOKBACK):
    if side == "BUY" and "ConfirmedPivotHigh3" in df.columns:
        value = df.iloc[idx]["ConfirmedPivotHigh3"]
        return None if pd.isna(value) else float(value)
    if side == "SELL" and "ConfirmedPivotLow3" in df.columns:
        value = df.iloc[idx]["ConfirmedPivotLow3"]
        return None if pd.isna(value) else float(value)

    confirm_upto = idx - lookback
    if confirm_upto < 0:
        return None
    hist = df.iloc[: confirm_upto + 1]
    if side == "BUY":
        swings = hist["PivotHigh3"].dropna()
    else:
        swings = hist["PivotLow3"].dropna()
    if swings.empty:
        return None
    return float(swings.iloc[-1])


def breaks_swing(row, swing_level, side):
    if swing_level is None:
        return False
    high = float(row["High"])
    low = float(row["Low"])
    if side == "BUY":
        return high > swing_level
    return low < swing_level


def detect_auto_trade(df, expected_side, min_index):
    df = prepare_detection_frame(df, lookback=PIVOT_LOOKBACK)
    start_index = max(min_index, 0)
    for idx in range(start_index, len(df)):
        row = df.iloc[idx]
        if is_first_candle_time(row["Time"]):
            continue
        if not good_candle(row):
            continue

        close = float(row["Close"])
        open_ = float(row["Open"])
        ema = float(row["EMA"])
        if not body_is_30pct_on_side_of_ema(row, expected_side):
            continue

        swing = get_latest_confirmed_swing(df, idx, expected_side, lookback=PIVOT_LOOKBACK)
        if not breaks_swing(row, swing, expected_side):
            continue

        if expected_side == "BUY":
            # BUY only when candle close is above EMA and candle is positive.
            if close > ema and close > open_:
                return idx
        elif expected_side == "SELL":
            # SELL only when candle close is below EMA and candle is negative.
            if close < ema and close < open_:
                return idx
    return None


def detect_first_trade(df, min_index=0):
    buy_idx = detect_auto_trade(df, "BUY", min_index)
    sell_idx = detect_auto_trade(df, "SELL", min_index)

    if buy_idx is None and sell_idx is None:
        return None, None
    if buy_idx is None:
        return "SELL", sell_idx
    if sell_idx is None:
        return "BUY", buy_idx
    if buy_idx <= sell_idx:
        return "BUY", buy_idx
    return "SELL", sell_idx


def normalize_trade_side(text):
    t = text.strip().lower()
    if t in ["b", "buy", "by"]:
        return "BUY"
    if t in ["s", "sell", "sel"]:
        return "SELL"
    return None


def ask_manual_trade_entry(df, min_index, forced_side=None, title="Manual Entry", show_title=True, show_forced_side=True, context_renderer=None, open_trade_context=None):
    while True:
        try:
            if context_renderer is not None:
                clear()
                context_renderer()

            if show_title and title:
                print()
                print_section(title)
            if show_forced_side and forced_side in ["BUY", "SELL"]:
                print_kv("Trade Type", f"fixed to {forced_side}")

            prompt_labels = ["Enter Date", "Enter Time"]
            if forced_side not in ["BUY", "SELL"]:
                prompt_labels.append("Enter Trade")
            prompt_width = max(PROMPT_LABEL_WIDTH, max(len(label) for label in prompt_labels))

            print()
            print_line()
            date = normalize_date(prompt_input("Enter Date", inline=True, label_width=prompt_width))
            time = normalize_time(prompt_input("Enter Time", inline=True, label_width=prompt_width))

            if is_first_candle_time(time):
                raise ValueError(f"First candle at {FIRST_CANDLE_TIME} cannot be used for entry or exit.")

            if forced_side in ["BUY", "SELL"]:
                side = forced_side
            else:
                while True:
                    side_raw = prompt_input("Enter Trade", inline=True, label_width=prompt_width)
                    side = normalize_trade_side(side_raw)
                    if side:
                        break
                    print("Invalid trade type. Enter Buy or Sell.")

            mask = (df["Date"] == date) & (df["Time"] == time) & (df.index >= min_index)
            matches = df[mask]

            if matches.empty:
                any_match = df[(df["Date"] == date) & (df["Time"] == time)]
                if any_match.empty:
                    raise ValueError(describe_missing_candle(df, date, time))
                raise ValueError("Candle exists, but it is before the current allowed position.")

            idx = int(matches.index[0])
            price = ask_entry_price(df.loc[idx, "Close"])

            if context_renderer is not None:
                clear()
                if forced_side in ["BUY", "SELL"] and open_trade_context is not None:
                    print_trade_review(
                        df=df,
                        open_side=open_trade_context["side"],
                        open_idx=open_trade_context["idx"],
                        open_price=open_trade_context["price"],
                        qty=open_trade_context["qty"],
                        new_side=side,
                        new_idx=idx,
                        new_price=price,
                    )
                else:
                    context_renderer()

            print()
            if forced_side not in ["BUY", "SELL"]:
                print_section("Confirm Entry")
                print_kv("Date", date)
                print_kv("Time", time)
                print_kv("Trade", format_side(side))
                print()
                print_dual_menu_options("1 Accept", "2 Re-Enter")
                confirm = prompt_input("Select Option")
            else:
                confirm = prompt_input("Input", leading_blank=False)
            if confirm == "2":
                continue
            if confirm != "1":
                print("Invalid option.")
                continue

            return idx, price, side
        except Exception as e:
            print()
            print_kv("Input Error", e)
            print_menu_option("1 Rewrite Entry")
            print_menu_option("2 Cancel")
            opt = prompt_input("Select Option")
            if opt == "1":
                continue
            if opt == "2":
                return None, None, None
            print("Invalid option.")


def format_side(side: str) -> str:
    if side == "BUY":
        return f"{ANSI_BOLD}{ANSI_GREEN}BUY{ANSI_RESET}"
    if side == "SELL":
        return f"{ANSI_BOLD}{ANSI_RED}SELL{ANSI_RESET}"
    return side


def format_price(value) -> str:
    return f"{ANSI_BOLD}{ANSI_YELLOW}{float(value):.2f}{ANSI_RESET}"


def color_by_sign(text: str, value: float) -> str:
    color = ANSI_GREEN if value > 0 else ANSI_RED if value < 0 else ANSI_YELLOW
    return f"{ANSI_BOLD}{color}{text}{ANSI_RESET}"


def points_text(value: float, width: int = 0) -> str:
    base = f"{value:.2f}"
    if width > 0:
        base = f"{base:>{width}}"
    return color_by_sign(base, value)


def format_inr_accounting(value: float) -> str:
    abs_value = abs(float(value))
    whole, frac = f"{abs_value:.2f}".split(".")

    if len(whole) > 3:
        last3 = whole[-3:]
        rest = whole[:-3]
        groups = []
        while len(rest) > 2:
            groups.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.insert(0, rest)
        whole = ",".join(groups + [last3])

    amt = f"{CURRENCY_SYMBOL} {whole}.{frac}"
    if float(value) < 0:
        return f"({amt})"
    return amt


def amount_text(value: float, width: int = 0) -> str:
    base = format_inr_accounting(value)
    if width > 0:
        base = f"{base:>{width}}"
    return color_by_sign(base, value)


def signed_value_text(value: float) -> str:
    return color_by_sign(f"{float(value):+.2f}", float(value))


def review_time_text(value) -> str:
    return format_output_time(value).replace(".", ":")


def terminal_text_width(text: str) -> int:
    return len(ANSI_ESCAPE_RE.sub("", str(text)))


def terminal_pad(text: str, width: int) -> str:
    visible_width = terminal_text_width(text)
    padding = max(0, width - visible_width)
    return f"{text}{' ' * padding}"


def print_trade_review(df, open_side, open_idx, open_price, qty, new_side, new_idx, new_price):
    open_row = df.iloc[int(open_idx)]
    new_row = df.iloc[int(new_idx)]
    preview = build_trade_row(
        df=df,
        side=open_side,
        entry_idx=int(open_idx),
        exit_idx=int(new_idx),
        entry_price=float(open_price),
        exit_price=float(new_price),
        qty=float(qty),
    )

    title = " TRADE REVIEW "
    pad = max(0, TRADE_REVIEW_TOTAL_WIDTH - len(title))
    left = pad // 2
    right = pad - left

    left_lines = [
        f"Type : {format_side(open_side)}",
        f"Price: {format_price(open_price)}",
        f"Date : {format_output_date(open_row['Date'])}",
        f"Time : {review_time_text(open_row['Time'])}",
    ]
    right_lines = [
        f"Type : {format_side(new_side)}",
        f"Price: {format_price(new_price)}",
        f"Date : {format_output_date(new_row['Date'])}",
        f"Time : {review_time_text(new_row['Time'])}",
    ]
    print()
    print(f"{ANSI_BOLD}{ANSI_CYAN}{'═' * left}{title}{'═' * right}{ANSI_RESET}")
    print()
    print(
        f"{terminal_pad(f'{ANSI_BOLD}OPEN TRADE{ANSI_RESET}', TRADE_REVIEW_LEFT_WIDTH)}"
        f"{terminal_pad(f'{ANSI_BOLD}NEW SIGNAL{ANSI_RESET}', TRADE_REVIEW_RIGHT_WIDTH)}"
    )
    print(
        f"{terminal_pad('─' * TRADE_REVIEW_SPLIT_WIDTH, TRADE_REVIEW_LEFT_WIDTH)}"
        f"{terminal_pad('─' * TRADE_REVIEW_SPLIT_WIDTH, TRADE_REVIEW_RIGHT_WIDTH)}"
    )
    for left_line, right_line in zip(left_lines, right_lines):
        print(
            f"{terminal_pad(left_line, TRADE_REVIEW_LEFT_WIDTH)}"
            f"{terminal_pad(right_line, TRADE_REVIEW_RIGHT_WIDTH)}"
        )
    print()
    print(f"{ANSI_BOLD}{ANSI_CYAN}{'═' * TRADE_REVIEW_TOTAL_WIDTH}{ANSI_RESET}")
    print(f"{ANSI_BOLD}P&L SUMMARY{ANSI_RESET}")
    print("─" * TRADE_REVIEW_TOTAL_WIDTH)
    print(f"Points : {signed_value_text(float(preview['PL Points']))}")
    print(f"Amount : {signed_value_text(float(preview['PL Amt']))}")
    print(f"{ANSI_BOLD}{ANSI_CYAN}{'═' * TRADE_REVIEW_TOTAL_WIDTH}{ANSI_RESET}")
    print_dual_menu_options("1 Accept Exit", "2 Re-Enter", gap=9)



# MAIN FUNCTIONS


def handle_auto_or_manual_entry(df, expected_side, min_index, entry_mode, manual_min_index=None, open_side=None, open_idx=None, open_price=None, qty=None, manual_title="Manual Entry", manual_show_title=True, manual_show_forced_side=True):

    if manual_min_index is None:
        manual_min_index = min_index

    manual_context_renderer = None
    open_trade_context = None
    if open_side in ["BUY", "SELL"] and open_idx is not None and open_price is not None:
        def manual_context_renderer():
            print_open_position(df, open_side, int(open_idx), float(open_price))
        if qty is not None:
            open_trade_context = {
                "side": open_side,
                "idx": int(open_idx),
                "price": float(open_price),
                "qty": float(qty),
            }

    if entry_mode == "MANUAL":
        return ask_manual_trade_entry(
            df,
            manual_min_index,
            forced_side=expected_side,
            title=manual_title,
            show_title=manual_show_title,
            show_forced_side=manual_show_forced_side,
            context_renderer=manual_context_renderer,
            open_trade_context=open_trade_context,
        )

    scan_start = min_index

    while True:
        if expected_side in ["BUY", "SELL"]:
            idx = detect_auto_trade(df, expected_side, scan_start)
            side = expected_side
        else:
            side, idx = detect_first_trade(df, scan_start)

        if idx is None:
            print("\nNo more automatic signals found.")
            print_menu_option("1 Manual Override")
            print_menu_option("2 Exit Trading")

            opt = prompt_input("Select Option")

            if opt == "1":
                return ask_manual_trade_entry(df, manual_min_index, forced_side=expected_side, title="Manual Override", context_renderer=manual_context_renderer, open_trade_context=open_trade_context)

            if opt == "2":
                return None, None, None

            print("Invalid option.")
            continue

        row = df.iloc[idx]

        print()
        print(UI_LINE)
        print_section("AUTO TRADE DETECTED")
        print(UI_LINE)
        print()
        print_kv("Trade Type", format_side(side))
        print_kv("Date", row["Date"])
        print_kv("Time", row["Time"])
        print_kv("Price", format_price(row["Close"]))

        if open_side in ["BUY", "SELL"] and open_idx is not None and open_price is not None and qty is not None:
            preview = build_trade_row(
                df=df,
                side=open_side,
                entry_idx=int(open_idx),
                exit_idx=int(idx),
                entry_price=float(open_price),
                exit_price=float(row["Close"]),
                qty=float(qty),
            )
            print()
            print_section("IF EXITED HERE")
            print_kv("Net P&L", f"{amount_text(float(preview['PL Amt']))}   ({points_text(float(preview['PL Points']))} pts)")
            print_kv_pair("Max MTM", amount_text(float(preview["Max MTM Amt"])), "Price", format_price(preview["Max MTM Price"]))
            print_kv_pair("Date", preview["Max MTM Date"], "Time", preview["Max MTM Time"])
        print()

        opt1 = f"{ANSI_BOLD}{ANSI_GREEN}{ICON_LIST} 1 - Accept Trade{ANSI_RESET}"
        opt2 = f"{ANSI_BOLD}{ANSI_RED}{ICON_LIST} 2 - Reject Trade{ANSI_RESET}"
        opt3 = f"{ANSI_BOLD}{ANSI_YELLOW}{ICON_LIST} 3 Manual Override{ANSI_RESET}"

        print(opt1)
        print(opt2)
        print(opt3)

        opt = prompt_input("Select Option")

        if opt == "1":
            return idx, float(row["Close"]), side

        if opt == "2":
            scan_start = idx + 1
            continue

        if opt == "3":
            return ask_manual_trade_entry(df, manual_min_index, forced_side=expected_side, title="Manual Override", context_renderer=manual_context_renderer, open_trade_context=open_trade_context)

        print("Invalid option.")


def scan_for_next_trade(df, current_side, current_idx, current_price, qty, entry_mode):

    # Opposite side must close the current trade
    next_side = "SELL" if current_side == "BUY" else "BUY"

    next_idx, next_price, detected_side = handle_auto_or_manual_entry(
        df=df,
        expected_side=next_side,
        min_index=current_idx + 1,
        entry_mode=entry_mode,
        open_side=current_side,
        open_idx=current_idx,
        open_price=current_price,
        qty=qty,
        manual_title=None,
        manual_show_title=False,
        manual_show_forced_side=False,
    )

    if next_idx is None:
        return None, None, None

    return detected_side, next_idx, next_price

# MAIN FUNCTIONS



def build_trade_row(df, side, entry_idx, exit_idx, entry_price, exit_price, qty):
    entry_row = df.iloc[entry_idx]
    exit_row = df.iloc[exit_idx]
    segment = df.iloc[entry_idx: exit_idx + 1]

    if side == "BUY":
        pl_points = float(exit_price - entry_price)
        mtm_idx = int(segment["High"].idxmax())
        mtm_price = float(df.loc[mtm_idx, "High"])
        mtm_amt = float((mtm_price - entry_price) * qty)
    else:
        pl_points = float(entry_price - exit_price)
        mtm_idx = int(segment["Low"].idxmin())
        mtm_price = float(df.loc[mtm_idx, "Low"])
        mtm_amt = float((entry_price - mtm_price) * qty)

    return {
        "Trade": side,
        "Entry Date": format_output_date(entry_row["Date"]),
        "Entry Time": format_output_time(entry_row["Time"]),
        "Entry Price": round(float(entry_price), 2),
        "Exit Date": format_output_date(exit_row["Date"]),
        "Exit Time": format_output_time(exit_row["Time"]),
        "Exit Price": round(float(exit_price), 2),
        "Qty": qty,
        "PL Points": round(pl_points, 2),
        "PL Amt": round(pl_points * qty, 2),
        "Max MTM Date": format_output_date(df.loc[mtm_idx, "Date"]),
        "Max MTM Time": format_output_time(df.loc[mtm_idx, "Time"]),
        "Max MTM Price": round(mtm_price, 2),
        "Max MTM Amt": round(mtm_amt, 2),
    }


def print_trade_closed(trade_row):
    print()
    print(UI_LINE)
    print(f"{ICON_SECTION} TRADE CLOSED")
    print(UI_LINE)
    print()
    print_kv("Trade Type", trade_row["Trade"])
    print()
    print(f"{'Stage':<10}{'Date':<12}{'Time':<11}{'Price':>8}")
    print(UI_LINE)
    print(
        f"{'Entry':<10}"
        f"{trade_row['Entry Date']:<12}"
        f"{trade_row['Entry Time']:<11}"
        f"{trade_row['Entry Price']:>8.2f}"
    )
    print(
        f"{'Max MTM':<10}"
        f"{trade_row['Max MTM Date']:<12}"
        f"{trade_row['Max MTM Time']:<11}"
        f"{trade_row['Max MTM Price']:>8.2f}"
    )
    print(
        f"{'Exit':<10}"
        f"{trade_row['Exit Date']:<12}"
        f"{trade_row['Exit Time']:<11}"
        f"{trade_row['Exit Price']:>8.2f}"
    )
    print()
    print(UI_LINE)
    print_kv("P&L Points", points_text(float(trade_row["PL Points"])))
    print_kv("P&L Amount", amount_text(float(trade_row["PL Amt"])))
    print_kv("MTM Amount", amount_text(float(trade_row["Max MTM Amt"])))


def print_open_position(df, side, idx, price):
    row = df.iloc[idx]
    print()
    print_section("Current Open Trade")
    print()
    print_kv("Trade Type", format_side(side))
    print_kv("Price", format_price(price))
    print_kv("Date", row["Date"])
    print_kv("Time", row["Time"])


def summary_dataframe(rows):
    if not rows:
        return pd.DataFrame(columns=SUMMARY_COLUMNS)
    return normalize_output_sheet(pd.DataFrame(rows)[SUMMARY_COLUMNS])


def show_summary(rows):
    out = summary_dataframe(rows)
    print(UI_LINE)
    print_section("TRADE SUMMARY")
    print(UI_LINE)
    print()
    if out.empty:
        print("No closed trades yet.")
        return out

    print(f"{'No':<4}{'Type':<6}{'Entry Date':<12}{'Time':<9}{'Price':>8}  {'Exit Time':<10}{'Price':>8}  {'Pts':>7}  {'P&L':>12}")
    print(UI_LINE)
    net_points = 0.0
    net_pl = 0.0
    net_mtm_pl = 0.0
    for i, r in enumerate(rows, 1):
        net_points += float(r["PL Points"])
        net_pl += float(r["PL Amt"])
        pl_points = float(r["PL Points"])
        pl_amt = float(r["PL Amt"])
        mtm_amt = float(r["Max MTM Amt"])
        net_mtm_pl += mtm_amt

        print(
            f"{i:<4}{r['Trade']:<6}{r['Entry Date']:<12}{r['Entry Time']:<9}"
            f"{float(r['Entry Price']):>8.2f}  {r['Exit Time']:<10}"
            f"{float(r['Exit Price']):>8.2f}  {points_text(pl_points, 7)}  {amount_text(pl_amt, 12)}"
        )
        print(
            f"{'':<4}{'MTM':<6}{r['Max MTM Date']:<12}{r['Max MTM Time']:<9}"
            f"{float(r['Max MTM Price']):>8.2f}  {'':<10}{'':>8}  {'':>7}  {amount_text(mtm_amt, 12)}"
        )
        print()

    print(UI_LINE)
    print_kv("Total Trades", len(rows))
    print_kv("Net Points", points_text(net_points))
    print_kv("Net P&L", amount_text(net_pl))
    print_kv("Net MTM P&L", amount_text(net_mtm_pl))
    return out

def export_summary(out_df, scrip, show_saved_message=True):
    path = SUMMARY_FOLDER / f"{scrip}.xlsx"

    if path.exists():
        try:
            existing = pd.read_excel(path)
        except Exception:
            existing = pd.DataFrame(columns=SUMMARY_COLUMNS)
    else:
        existing = pd.DataFrame(columns=SUMMARY_COLUMNS)

    existing = normalize_output_sheet(existing)
    incoming = normalize_output_sheet(out_df.copy())
    if all(col in incoming.columns for col in SUMMARY_COLUMNS):
        incoming = incoming[SUMMARY_COLUMNS]

    combined = pd.concat([existing, incoming], ignore_index=True)
    combined = normalize_output_sheet(combined)
    if all(col in combined.columns for col in SUMMARY_COLUMNS):
        combined = combined[SUMMARY_COLUMNS]
    combined = combined.drop_duplicates().reset_index(drop=True)

    combined.to_excel(path, index=False)
    if show_saved_message:
        print()
        print_kv("Saved", str(path))


def post_trade_menu(rows, scrip):
    while True:
        print()
        print_section("Trade Menu")
        print_menu_option("1 Continue Trading")
        print_menu_option("2 Show Summary")
        print_menu_option("3 Exit")
        ch = prompt_input("Select Option")

        if ch == "1":
            return "continue"

        if ch == "2":
            clear()
            out = show_summary(rows)
            print()
            print_section("Summary Options")
            print_menu_option("1 Export Excel")
            print_menu_option("2 Back to Trade")
            sub = prompt_input("Select Option")
            if sub == "1":
                export_summary(out, scrip)
            return "continue"

        if ch == "3":
            return "exit"

        print("Invalid option.")


def run_trade_loop(df, qty, scrip, entry_mode):
    
    first_idx, first_price, first_side = handle_auto_or_manual_entry(
        df=df,
        expected_side=None,
        min_index=0,
        entry_mode=entry_mode,
        manual_min_index=0,
        manual_title="First Entry",
    )
    if first_idx is None:
        return []

    current_side = first_side
    current_idx = first_idx
    current_price = first_price
    closed_rows = []

    while True:
        next_side, next_idx, next_price = scan_for_next_trade(
            df=df,
            current_side=current_side,
            current_idx=current_idx,
            current_price=current_price,
            qty=qty,
            entry_mode=entry_mode,
        )
        if next_idx is None:
            return closed_rows

        closed_trade = build_trade_row(
            df=df,
            side=current_side,
            entry_idx=current_idx,
            exit_idx=next_idx,
            entry_price=current_price,
            exit_price=next_price,
            qty=qty,
        )
        closed_rows.append(closed_trade)
        export_summary(summary_dataframe([closed_trade]), scrip, show_saved_message=False)

        current_side = next_side
        current_idx = next_idx
        current_price = next_price


def main():
    while True:
        try:

            scrip, df, suggested_start = choose_scrip_and_load()

            if df is None:
                return

            df_from_start, start, qty = ask_start_and_qty(df, scrip, suggested_start)

            entry_mode = "MANUAL"

            header("Trade Session")
            print_kv("Scrip", scrip.upper())
            print_kv("Start Date", start)
            print_kv("Quantity", qty)
            print_kv("Entry Mode", "Manual Next Entry")

            rows = run_trade_loop(df_from_start, qty, scrip, entry_mode)

            header("Session Ended")

            show_summary(rows)

            if rows:
                print()
                print_kv("Saved", str(SUMMARY_FOLDER / f"{scrip}.xlsx"))

            return

        except Exception as e:

            print()
            print_kv("Error", e)

            print_menu_option("1 Restart")
            print_menu_option("2 Exit")

            opt = prompt_input("Select Option")

            if opt != "1":
                return



if __name__ == "__main__":
    main()





