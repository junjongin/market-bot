import requests
import yfinance as yf

# =========================
# Telegram 설정
# =========================
TOKEN = "bot8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4"
CHAT_ID = "7701788482"

# =========================
# 시장 데이터
# =========================
nasdaq = yf.Ticker("^IXIC").history(period="1d")
sp500 = yf.Ticker("^GSPC").history(period="1d")
btc = yf.Ticker("BTC-USD").history(period="1d")
oil = yf.Ticker("CL=F").history(period="1d")

nasdaq_price = round(nasdaq["Close"].iloc[-1],2)
sp500_price = round(sp500["Close"].iloc[-1],2)
btc_price = round(btc["Close"].iloc[-1],2)
oil_price = round(oil["Close"].iloc[-1],2)

# =========================
# 미국 포트폴리오
# =========================
us_portfolio = [
"JNJ","AAPL","MSFT","SCHD","QQQM","JEPI","GOOGL","JEPQ","IEF","TLT"
]

# =========================
# 국내 포트폴리오
# (Yahoo Finance 티커)
# =========================
kr_portfolio = {
"Samsung Electronics":"005930.KS"
}

# =========================
# 미국 종목 데이터
# =========================
us_text = ""
for ticker in us_portfolio:
    data = yf.Ticker(ticker).history(period="1d")
    price = round(data["Close"].iloc[-1],2)
    us_text += f"{ticker}: ${price}\n"

# =========================
# 한국 종목 데이터
# =========================
kr_text = ""
for name,ticker in kr_portfolio.items():
    data = yf.Ticker(ticker).history(period="1d")
    price = round(data["Close"].iloc[-1],0)
    kr_text += f"{name}: ₩{price}\n"

# =========================
# 메시지 구성
# =========================
message = f"""
📊 Daily Market Report

🌎 Global Market
NASDAQ: {nasdaq_price}
S&P500: {sp500_price}
BTC: ${btc_price}
Oil: ${oil_price}

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

requests.post(url, data=payload)
