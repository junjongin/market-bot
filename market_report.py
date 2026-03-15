import requests
import yfinance as yf

# =========================
# Telegram 설정
# =========================
TOKEN = "8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4"
CHAT_ID = "7701788482"

# =========================
# 알림 기준
# =========================
ALERT_UP = 2.0
ALERT_DOWN = -2.0
CRITICAL_DOWN = -3.0   # 별도 경고 메시지 기준

# =========================
# 유틸
# =========================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    response = requests.post(url, data=payload)
    print(response.text)


def get_color(change):
    if change is None:
        return "⚪"
    if change > 0:
        return "🔴"
    if change < 0:
        return "🔵"
    return "⚪"


def get_price_and_change(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
        if data.empty or len(data) < 2:
            return None, None

        close_today = float(data["Close"].iloc[-1])
        close_prev = float(data["Close"].iloc[-2])

        if close_prev == 0:
            return close_today, None

        change_pct = ((close_today - close_prev) / close_prev) * 100
        return close_today, change_pct

    except Exception:
        return None, None


def format_market_line(name, ticker):
    price, change = get_price_and_change(ticker)

    if price is None:
        return f"⚪ {name}: 데이터 없음"

    color = get_color(change)

    if name in ["Bitcoin", "Brent Oil"]:
        return f"{color} {name}: ${price:,.2f} ({change:+.2f}%)"
    elif name == "USD/KRW":
        return f"{color} {name}: {price:,.2f} ({change:+.2f}%)"
    else:
        return f"{color} {name}: {price:,.2f} ({change:+.2f}%)"


# =========================
# 저장소
# =========================
us_gainers = []
us_losers = []
kr_gainers = []
kr_losers = []
all_positions = []
alerts = []
critical_alerts = []


def analyze_ticker(name, ticker, market):
    price, change = get_price_and_change(ticker)

    if price is None:
        return

    color = get_color(change)

    if market == "US":
        line = f"{color} {name}: ${price:,.2f} ({change:+.2f}%)"
        if change > 0:
            us_gainers.append((change, line, name, market))
        elif change < 0:
            us_losers.append((change, line, name, market))
        all_positions.append((change, line, name, market))
    else:
        line = f"{color} {name}: ₩{price:,.0f} ({change:+.2f}%)"
        if change > 0:
            kr_gainers.append((change, line, name, market))
        elif change < 0:
            kr_losers.append((change, line, name, market))
        all_positions.append((change, line, name, market))

    # 일반 알림
    if change >= ALERT_UP:
        alerts.append(f"🚀 {market} {name}: {change:+.2f}%")
    elif change <= ALERT_DOWN:
        alerts.append(f"⚠️ {market} {name}: {change:+.2f}%")

    # 별도 하락 경고
    if change <= CRITICAL_DOWN:
        if market == "US":
            critical_alerts.append(f"🚨 {market} {name}: ${price:,.2f} ({change:+.2f}%)")
        else:
            critical_alerts.append(f"🚨 {market} {name}: ₩{price:,.0f} ({change:+.2f}%)")


# =========================
# 글로벌 시장
# =========================
market_tickers = {
    "NASDAQ": "^IXIC",
    "S&P500": "^GSPC",
    "Bitcoin": "BTC-USD",
    "Brent Oil": "BZ=F",
    "USD/KRW": "KRW=X",
}

market_lines = [format_market_line(name, ticker) for name, ticker in market_tickers.items()]
market_text = "\n".join(market_lines)

# =========================
# 미국 포트폴리오
# =========================
us_portfolio = [
    "JNJ",
    "AAPL",
    "MSFT",
    "SCHD",
    "QQQM",
    "JEPI",
    "GOOGL",
    "JEPQ",
    "IEF",
    "TLT",
]

for ticker in us_portfolio:
    analyze_ticker(ticker, ticker, "US")

# =========================
# 한국 포트폴리오
# =========================
kr_portfolio = {
    "Samsung Electronics": "005930.KS",
    "KODEX S&P500": "379800.KS",
    "KOSEF 200TR": "294400.KS",
    "TIGER 은행고배당플러스TOP10": "307710.KS",
    "PLUS 고배당주": "161510.KS",
    "ACE KRX금현물": "411060.KS",
    "TIGER 미국배당다우존스타겟데일리커버드콜": "458730.KS",
    "KIWOOM 국고채10년": "148070.KS",
    "RISE KIS국고채30년Enhanced": "439870.KS",
}

for name, ticker in kr_portfolio.items():
    analyze_ticker(name, ticker, "KR")

# =========================
# 정렬
# =========================
us_gainers.sort(key=lambda x: x[0], reverse=True)
us_losers.sort(key=lambda x: x[0])

kr_gainers.sort(key=lambda x: x[0], reverse=True)
kr_losers.sort(key=lambda x: x[0])

all_positions_sorted_up = sorted(all_positions, key=lambda x: x[0], reverse=True)
all_positions_sorted_down = sorted(all_positions, key=lambda x: x[0])

top_gainers = all_positions_sorted_up[:3]
top_losers = all_positions_sorted_down[:3]

top_gainers_text = "\n".join([f"🚀 {name} ({market}): {change:+.2f}%" for change, _, name, market in top_gainers]) if top_gainers else "없음"
top_losers_text = "\n".join([f"💥 {name} ({market}): {change:+.2f}%" for change, _, name, market in top_losers]) if top_losers else "없음"

us_gainers_text = "\n".join([line for _, line, _, _ in us_gainers]) if us_gainers else "없음"
us_losers_text = "\n".join([line for _, line, _, _ in us_losers]) if us_losers else "없음"

kr_gainers_text = "\n".join([line for _, line, _, _ in kr_gainers]) if kr_gainers else "없음"
kr_losers_text = "\n".join([line for _, line, _, _ in kr_losers]) if kr_losers else "없음"

alerts_text = "\n".join(alerts) if alerts else "없음"

market_summary = []
for line in market_lines:
    if "NASDAQ" in line or "S&P500" in line or "Bitcoin" in line or "USD/KRW" in line:
        market_summary.append(f"- {line}")

market_summary_text = "\n".join(market_summary)

# =========================
# 정규 리포트 메시지
# =========================
message = f"""📊 Daily Market Report

🌎 Global Market
{market_text}

🧭 Market Summary
{market_summary_text}

🚀 Top Movers
{top_gainers_text}

💥 Weakest Movers
{top_losers_text}

🇺🇸 US Gainers
{us_gainers_text}

🇺🇸 US Losers
{us_losers_text}

🇰🇷 KR Gainers
{kr_gainers_text}

🇰🇷 KR Losers
{kr_losers_text}

🚨 Alerts
{alerts_text}
"""

send_telegram_message(message)

# =========================
# 별도 하락 경고 메시지
# =========================
if critical_alerts:
    critical_message = "🚨 Critical Drop Alert (-3% 이하)\n\n" + "\n".join(critical_alerts)
    send_telegram_message(critical_message)
