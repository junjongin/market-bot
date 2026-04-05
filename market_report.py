import requests
import yfinance as yf
import os
from datetime import datetime, timedelta
import time

start_time = time.time()

# =========================
# Telegram 설정
# =========================
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# =========================
# 알림 기준
# =========================
ALERT_UP = 2.0
ALERT_DOWN = -2.0
CRITICAL_DOWN = -2.1  # 별도 경고 메시지 기준

# =========================
# 시간 / 장 상태
# =========================
def get_kst_time():
    return datetime.utcnow() + timedelta(hours=9)

def get_report_time_text():
    kst_now = get_kst_time()
    return kst_now.strftime("%Y-%m-%d %H:%M KST")

def get_market_status():
    kst_now = get_kst_time()
    weekday = kst_now.weekday()  # 월=0, 일=6

    # 한국장: 평일 09:00 ~ 15:30
    if weekday < 5:
        if ((kst_now.hour > 9) or (kst_now.hour == 9 and kst_now.minute >= 0)) and \
           ((kst_now.hour < 15) or (kst_now.hour == 15 and kst_now.minute <= 30)):
            kr_status = "OPEN"
        else:
            kr_status = "CLOSED"
    else:
        kr_status = "CLOSED"

    # 미국장: 단순 버전 (KST 기준 22:30 ~ 05:00)
    # 월~금 밤 + 다음날 새벽까지를 대략 반영
    if weekday < 5:
        if (kst_now.hour > 22 or (kst_now.hour == 22 and kst_now.minute >= 30) or kst_now.hour < 5):
            us_status = "OPEN"
        else:
            us_status = "CLOSED"
    else:
        us_status = "CLOSED"

    return kr_status, us_status


# 전역 장 상태를 먼저 확보
kr_status, us_status = get_market_status()

# =========================
# Telegram 전송
# =========================
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    response = requests.post(url, data=payload, timeout=20)
    print(response.text)

# =========================
# 유틸
# =========================
def get_color(change, market_open=True):
    if change is None:
        return "⚪" if market_open else "▫️"

    if market_open:
        if change > 0:
            return "🔴"
        if change < 0:
            return "🔵"
        return "⚪"
    else:
        # 장 마감 시 흐린 느낌 아이콘
        if change > 0:
            return "🔺"
        if change < 0:
            return "🔻"
        return "▫️"

def classify_change(change):
    if change is None:
        return "neutral"
    if change >= 1.0:
        return "strong_up"
    if change > 0:
        return "up"
    if change <= -1.0:
        return "strong_down"
    if change < 0:
        return "down"
    return "neutral"

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

    # 글로벌 지표별 장 상태 반영
    # 미국 지수/자산은 미국장 상태, 환율은 한국장 상태 기준
    market_open = True
    status_tag = ""

    if name in ["NASDAQ", "S&P500"]:
        market_open = (us_status == "OPEN")
        status_tag = "" if market_open else " (마감)"
    elif name == "USD/KRW":
        market_open = (kr_status == "OPEN")
        status_tag = "" if market_open else " (마감)"
    elif name in ["Bitcoin", "Brent Oil"]:
        # 24시간/장외 성격이 있어 음영 처리 없이 기본 표시
        market_open = True
        status_tag = ""

    color = get_color(change, market_open)

    if change is None:
        change_text = "N/A"
    else:
        change_text = f"{change:+.2f}%"

    if name in ["Bitcoin", "Brent Oil"]:
        return f"{color} {name}: ${price:,.2f} ({change_text})"
    elif name == "USD/KRW":
        return f"{color} {name}{status_tag}: {price:,.2f} ({change_text})"
    else:
        return f"{color} {name}{status_tag}: {price:,.2f} ({change_text})"

# =========================
# AI 시장 분석
# =========================
def build_ai_insight(market_changes, top_gainers, top_losers, us_gainers, us_losers, kr_gainers, kr_losers):
    insights = []

    nasdaq_change = market_changes.get("NASDAQ")
    sp500_change = market_changes.get("S&P500")
    btc_change = market_changes.get("Bitcoin")
    oil_change = market_changes.get("Brent Oil")
    fx_change = market_changes.get("USD/KRW")

    nasdaq_state = classify_change(nasdaq_change)
    sp500_state = classify_change(sp500_change)
    btc_state = classify_change(btc_change)
    oil_state = classify_change(oil_change)
    fx_state = classify_change(fx_change)

    # 1. 미국 시장 분위기
    if nasdaq_state in ["up", "strong_up"] and sp500_state in ["up", "strong_up"]:
        insights.append("US risk sentiment looks constructive as both NASDAQ and S&P500 are rising.")
    elif nasdaq_state in ["down", "strong_down"] and sp500_state in ["down", "strong_down"]:
        insights.append("US risk sentiment looks weak as both NASDAQ and S&P500 are falling.")
    elif nasdaq_state in ["up", "strong_up"] and sp500_state in ["down", "strong_down"]:
        insights.append("Tech is outperforming the broader market, suggesting selective risk-on sentiment.")
    elif nasdaq_state in ["down", "strong_down"] and sp500_state in ["up", "strong_up"]:
        insights.append("Broad market strength is present, but tech is lagging.")

    # 2. 비트코인
    if btc_state == "strong_up":
        insights.append("Bitcoin strength suggests speculative risk appetite is improving.")
    elif btc_state == "strong_down":
        insights.append("Bitcoin weakness suggests speculative sentiment is deteriorating.")

    # 3. 유가
    if oil_state == "strong_up":
        insights.append("Rising oil may add inflation pressure and could be a headwind for equities.")
    elif oil_state == "strong_down":
        insights.append("Falling oil may ease inflation concerns and support risk assets.")

    # 4. 환율
    if fx_state in ["up", "strong_up"]:
        insights.append("A stronger USD/KRW may weigh on Korean assets and foreign fund flows.")
    elif fx_state in ["down", "strong_down"]:
        insights.append("A softer USD/KRW may be supportive for Korean market sentiment.")

    # 5. 미국 vs 한국 포트폴리오
    us_strength = len(us_gainers) - len(us_losers)
    kr_strength = len(kr_gainers) - len(kr_losers)

    if us_strength > kr_strength:
        insights.append("US portfolio names are showing relatively stronger momentum than Korean holdings.")
    elif kr_strength > us_strength:
        insights.append("Korean portfolio names are showing relatively stronger momentum than US holdings.")

    # 6. Top mover
    if top_gainers:
        top_name = top_gainers[0][2]
        top_market = top_gainers[0][3]
        top_change = top_gainers[0][0]
        insights.append(f"The strongest portfolio mover is {top_name} ({top_market}, {top_change:+.2f}%).")

    if top_losers:
        weak_name = top_losers[0][2]
        weak_market = top_losers[0][3]
        weak_change = top_losers[0][0]
        insights.append(f"The weakest portfolio mover is {weak_name} ({weak_market}, {weak_change:+.2f}%).")

    if not insights:
        insights.append("Market signals are mixed and there is no strong directional edge right now.")

    return "\n".join([f"- {x}" for x in insights[:5]])

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

    market_open = (us_status == "OPEN") if market == "US" else (kr_status == "OPEN")
    color = get_color(change, market_open)
    status_tag = "" if market_open else " (마감)"

    if market == "US":
        line = f"{color} {name}{status_tag}: ${price:,.2f} ({change:+.2f}%)"
        if change > 0:
            us_gainers.append((change, line, name, market))
        elif change < 0:
            us_losers.append((change, line, name, market))
        all_positions.append((change, line, name, market))
    else:
        line = f"{color} {name}{status_tag}: ₩{price:,.0f} ({change:+.2f}%)"
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

market_lines = []
market_changes = {}

for name, ticker in market_tickers.items():
    price, change = get_price_and_change(ticker)
    market_changes[name] = change
    market_lines.append(format_market_line(name, ticker))

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

top_gainers_text = "\n".join(
    [f"🚀 {name} ({market}): {change:+.2f}%" for change, _, name, market in top_gainers]
) if top_gainers else "없음"

top_losers_text = "\n".join(
    [f"💥 {name} ({market}): {change:+.2f}%" for change, _, name, market in top_losers]
) if top_losers else "없음"

us_gainers_text = "\n".join([line for _, line, _, _ in us_gainers]) if us_gainers else "없음"
us_losers_text = "\n".join([line for _, line, _, _ in us_losers]) if us_losers else "없음"

kr_gainers_text = "\n".join([line for _, line, _, _ in kr_gainers]) if kr_gainers else "없음"
kr_losers_text = "\n".join([line for _, line, _, _ in kr_losers]) if kr_losers else "없음"

alerts_text = "\n".join(alerts) if alerts else "없음"

# =========================
# 시장 요약
# =========================
market_summary = []
for line in market_lines:
    if "NASDAQ" in line or "S&P500" in line or "Bitcoin" in line or "USD/KRW" in line:
        market_summary.append(f"- {line}")

market_summary_text = "\n".join(market_summary)

# =========================
# AI 분석
# =========================
ai_insight_text = build_ai_insight(
    market_changes,
    top_gainers,
    top_losers,
    us_gainers,
    us_losers,
    kr_gainers,
    kr_losers
)

# =========================
# 시간 / 상태 / 실행시간
# =========================
report_time = get_report_time_text()
elapsed = time.time() - start_time
elapsed_text = f"{elapsed:.1f}s"

kr_label = "🟢 장중" if kr_status == "OPEN" else "🌙 마감"
us_label = "🟢 장중" if us_status == "OPEN" else "🌙 마감"

# =========================
# 정규 리포트 메시지
# =========================
message = f"""📊 Daily Market Report
🕒 Data Time: {report_time}
🇰🇷 KR Market: {kr_label}
🇺🇸 US Market: {us_label}
⏱ Execution Time: {elapsed_text}

🤖 AI Market Insight
{ai_insight_text}

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
    critical_message = (
        f"🚨 Critical Drop Alert (-2% 이하)\n"
        f"🕒 Data Time: {report_time}\n\n"
        + "\n".join(critical_alerts)
    )
    send_telegram_message(critical_message)
