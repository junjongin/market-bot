import requests
import yfinance as yf

# =========================
# Telegram 설정
# =========================
TOKEN = "bot8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4"
CHAT_ID = "7701788482"

# =========================
# 색상 이모지
# =========================
def get_color(change):
    if change > 0:
        return "🔴"
    elif change < 0:
        return "🔵"
    return "⚪"

# =========================
# 가격 / 변동률 계산
# =========================
def get_price_and_change(ticker):
    data = yf.Ticker(ticker).history(period="5d")

    if data.empty or len(data) < 2:
        return None, None

    close_today = data["Close"].iloc[-1]
    close_prev = data["Close"].iloc[-2]
    change_pct = ((close_today - close_prev) / close_prev) * 100

    return close_today, change_pct

# =========================
# 글로벌 시장 포맷
# =========================
def format_market_line(name, ticker):
    price, change = get_price_and_change(ticker)

    if price is None:
        return f"{name}: 데이터 없음"

    color = get_color(change)

    if name in ["Bitcoin", "Brent Oil"]:
        return f"{color} {name}: ${price:,.2f} ({change:+.2f}%)"
    elif name == "USD/KRW":
        return f"{color} {name}: {price:,.2f} ({change:+.2f}%)"
    else:
        return f"{color} {name}: {price:,.2f} ({change:+.2f}%)"

# =========================
# 포트폴리오 종목 분석
# =========================
gainers = []
losers = []
flat = []

def analyze_ticker(name, ticker, is_us=True):
    price, change = get_price_and_change(ticker)

    if price is None:
        line = f"⚪ {name}: 데이터 없음"
        flat.append(line)
        return

    color = get_color(change)

    if is_us:
        line = f"{color} {name}: ${price:,.2f} ({change:+.2f}%)"
    else:
        line = f"{color} {name}: ₩{price:,.0f} ({change:+.2f}%)"

    if change > 0:
        gainers.append((change, line))
    elif change < 0:
        losers.append((change, line))
    else:
        flat.append(line)

# =========================
# 시장 지표
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
    analyze_ticker(ticker, ticker, is_us=True)

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
    analyze_ticker(name, ticker, is_us=False)

# =========================
# 정렬
# 상승: 큰 폭 상승 순
# 하락: 큰 폭 하락 순
# =========================
gainers.sort(key=lambda x: x[0], reverse=True)
losers.sort(key=lambda x: x[0])

gainers_text = "\n".join([line for _, line in gainers]) if gainers else "없음"
losers_text = "\n".join([line for _, line in losers]) if losers else "없음"
flat_text = "\n".join(flat) if flat else "없음"

# =========================
# 메시지 구성
# =========================
message = f"""📊 Daily Market Report

🌎 Global Market
{market_text}

📈 Gainers
{gainers_text}

📉 Losers
{losers_text}

⚪ Flat / No Data
{flat_text}
"""

# =========================
# Telegram 전송
# =========================
url = f"https://api.telegram.org/bot8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": message
}

response = requests.post(url, data=payload)
print(response.text)
