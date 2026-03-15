import requests
import yfinance as yf

# =========================
# 1. 설정 (Settings)
# =========================
TOKEN = "bot8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4"
CHAT_ID = "7701788482"

ALERT_UP = 2.0
ALERT_DOWN = -2.0
EMERGENCY_DROP = -3.0

# =========================
# 2. 유틸리티 함수
# =========================
def send_telegram(text):
    url = f"https://api.telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        res = requests.post(url, data=payload)
        print(f"전송 결과: {res.status_code}") # 200이 나오면 성공
    except Exception as e:
        print(f"전송 중 네트워크 오류: {e}")

def get_price_and_change(ticker):
    try:
        # 데이터를 넉넉히 7일치 가져옵니다 (주말 대비)
        data = yf.Ticker(ticker).history(period="7d", auto_adjust=False)
        if data.empty or len(data) < 2:
            return None, None
        close_today = float(data["Close"].iloc[-1])
        close_prev = float(data["Close"].iloc[-2])
        change_pct = ((close_today - close_prev) / close_prev) * 100
        return close_today, change_pct
    except Exception as e:
        print(f"데이터 로드 오류 ({ticker}): {e}")
        return None, None

# =========================
# 3. 데이터 수집 및 분석
# =========================
market_results = []
us_lines = []
kr_lines = []
all_positions = []

# 지수 데이터
markets = {"NASDAQ": "^IXIC", "S&P500": "^GSPC", "Bitcoin": "BTC-USD", "USD/KRW": "KRW=X"}
for name, t in markets.items():
    p, c = get_price_and_change(t)
    if p:
        color = "🔴" if c > 0 else "🔵" if c < 0 else "⚪"
        market_results.append(f"{color} {name}: {p:,.2f} ({c:+.2f}%)")

# 미국 포트폴리오
us_portfolio = ["JNJ", "AAPL", "MSFT", "SCHD", "QQQM", "JEPI", "GOOGL", "JEPQ", "IEF", "TLT"]
for t in us_portfolio:
    p, c = get_price_and_change(t)
    if p:
        color = "🔴" if c > 0 else "🔵" if c < 0 else "⚪"
        line = f"{color} {t}: ${p:,.2f} ({c:+.2f}%)"
        us_lines.append(line)
        all_positions.append((c, line, t, "US"))
        # 긴급 알림
        if c <= EMERGENCY_DROP:
            send_telegram(f"🚨 *[SUDDEN DROP]*\n{t}: {c:+.2f}% (${p:,.2f})")

# 한국 포트폴리오
kr_portfolio = {"Samsung Electronics": "005930.KS", "KODEX S&P500": "379800.KS"} # 테스트용 2개만 우선
for n, t in kr_portfolio.items():
    p, c = get_price_and_change(t)
    if p:
        color = "🔴" if c > 0 else "🔵" if c < 0 else "⚪"
        line = f"{color} {n}: ₩{p:,.0f} ({c:+.2f}%)"
        kr_lines.append(line)
        all_positions.append((c, line, n, "KR"))
        if c <= EMERGENCY_DROP:
            send_telegram(f"🚨 *[SUDDEN DROP]*\n{n}: {c:+.2f}% (₩{p:,.0f})")

# =========================
# 4. 메시지 조립 및 전송
# =========================
market_text = "\n".join(market_results)
us_text = "\n".join(us_lines) if us_lines else "데이터 없음"
kr_text = "\n".join(kr_lines) if kr_lines else "데이터 없음"

# 상위/하위 3개 추출
all_positions.sort(key=lambda x: x[0], reverse=True)
top_text = "\n".join([f"🚀 {n}: {c:+.2f}%" for c, l, n, m in all_positions[:3]])
worst_text = "\n".join([f"💥 {n}: {c:+.2f}%" for c, l, n, m in all_positions[-3:]])

final_msg = f"""*📊 Market Report*

*🌎 Global Market*
{market_text}

*🔥 Top 3*
{top_text}

*💧 Worst 3*
{worst_text}

*🇺🇸 US Portfolio*
{us_text}

*🇰🇷 KR Portfolio*
{kr_text}
"""

send_telegram(final_msg)
