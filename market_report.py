import requests
import yfinance as yf

# =========================
# Telegram 설정
# =========================
TOKEN = "bot8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4"
CHAT_ID = "7701788482"

# =========================
# 공통 함수
# =========================
def get_price_and_change(ticker):
    data = yf.Ticker(ticker).history(period="5d")

    if data.empty or len(data) < 2:
        return None, None

    close_today = data["Close"].iloc[-1]
    close_prev = data["Close"].iloc[-2]
    change_pct = ((close_today - close_prev) / close_prev) * 100

    return close_today, change_pct


def format_us_line(ticker):
    price, change = get_price_and_change(ticker)
    if price is None:
        return f"{ticker}: 데이터 없음"
    return f"{ticker}: ${price:,.2f} ({change:+.2f}%)"


def format_kr_line(name, ticker):
    price, change = get_price_and_change(ticker)
    if price is None:
        return f"{name}: 데이터 없음"
    return f"{name}: ₩{price:,.0f} ({change:+.2f}%)"


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

market_text_lines = []
for name, ticker in market_tickers.items():
    price, change = get_price_and_change(ticker)
    if price is None:
        market_text_lines.append(f"{name}: 데이터 없음")
    else:
        if name in ["Bitcoin", "Brent Oil"]:
            market_text_lines.append(f"{name}: ${price:,.2f} ({change:+.2f}%)")
        elif name == "USD/KRW":
            market_text_lines.append(f"{name}: {price:,.2f} ({change:+.2f}%)")
        else:
            market_text_lines.append(f"{name}: {price:,.2f} ({change:+.2f}%)")

market_text = "\n".join(market_text_lines)

# =========================
# 미국 포트폴리오
# =========================
us_portfolio = [
    "JNJ", "AAPL", "MSFT", "SCHD", "QQQM",
    "JEPI", "GOOGL", "JEPQ", "IEF", "TLT"
]

us_lines = [format_us_line(ticker) for ticker in us_portfolio]
us_text = "\n".join(us_lines)

# =========================
# 국내 포트폴리오
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
    "RISE KIS국고채30년Enhanced": "439870.KS"
}

kr_lines = [format_kr_line(name, ticker) for name, ticker in kr_portfolio.items()]
kr_text = "\n".join(kr_lines)

# =========================
# 메시지 구성
# =========================
message = f"""📊 Daily Market Report

🌎 Global Market
{market_text}

🇺🇸 US Portfolio
{us_text}

🇰🇷 KR Portfolio
{kr_text}
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
