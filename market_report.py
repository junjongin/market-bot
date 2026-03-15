import requests
import yfinance as yf

# =========================
# 1. 설정 (기존 정보 유지)
# =========================
TOKEN = "8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4"
CHAT_ID = "7701788482"

ALERT_UP = 2.0
ALERT_DOWN = -2.0
EMERGENCY_DROP = -3.0

# =========================
# 2. 유틸리티 함수 (안정성 강화)
# =========================
def send_telegram_basic(text):
    """기존에 성공했던 방식 그대로 전송 (마크다운 제거)"""
    url = f"https://api.telegram.org{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text
    }
    try:
        res = requests.post(url, data=payload)
        print(f"전송 결과: {res.status_code}") 
    except Exception as e:
        print(f"연결 오류: {e}")

def get_price_and_change(ticker):
    try:
        data = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
        if data.empty or len(data) < 2:
            return None, None
        close_today = float(data["Close"].iloc[-1])
        close_prev = float(data["Close"].iloc[-2])
        change_pct = ((close_today - close_prev) / close_prev) * 100
        return close_today, change_pct
    except:
        return None, None

# =========================
# 3. 데이터 분석 로직
# =========================
market_lines = []
us_lines = []
kr_lines = []
alerts = []

# 지수 분석
markets = {"NASDAQ": "^IXIC", "S&P500": "^GSPC", "Bitcoin": "BTC-USD", "USD/KRW": "KRW=X"}
for name, t in markets.items():
    p, c = get_price_and_change(t)
    if p:
        color = "🔴" if c > 0 else "🔵" if c < 0 else "⚪"
        market_lines.append(f"{color} {name}: {p:,.2f} ({c:+.2f}%)")

# 미국 종목 분석 (긴급 알림 포함)
us_portfolio = ["JNJ", "AAPL", "MSFT", "SCHD", "QQQM", "JEPI", "GOOGL", "JEPQ", "IEF", "TLT"]
for t in us_portfolio:
    p, c = get_price_and_change(t)
    if p:
        color = "🔴" if c > 0 else "🔵" if c < 0 else "⚪"
        line = f"{color} {t}: ${p:,.2f} ({c:+.2f}%)"
        us_lines.append(line)
        if c <= EMERGENCY_DROP:
            send_telegram_basic(f"🚨 [SUDDEN DROP] {t}\n현재가: ${p:,.2f} ({c:+.2f}%)")

# 한국 종목 분석
kr_portfolio = {"Samsung Electronics": "005930.KS", "KODEX S&P500": "379800.KS"}
for n, t in kr_portfolio.items():
    p, c = get_price_and_change(t)
    if p:
        color = "🔴" if c > 0 else "🔵" if c < 0 else "⚪"
        line = f"{color} {n}: ₩{p:,.0f} ({c:+.2f}%)"
        kr_lines.append(line)

# =========================
# 4. 메시지 조립 및 전송 (기존 방식처럼 단순하게)
# =========================
message = "📊 Daily Market Report\n\n"

message += "🌎 Global Market\n"
message += "\n".join(market_lines) + "\n\n"

message += "🇺🇸 US Portfolio\n"
message += "\n".join(us_lines) + "\n\n"

message += "🇰🇷 KR Portfolio\n"
message += "\n".join(kr_lines)

# 최종 전송
send_telegram_basic(message)
