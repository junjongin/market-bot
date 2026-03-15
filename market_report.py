import requests
import yfinance as yf
import os

# =========================
# 1. 설정 (Settings)
# =========================
TOKEN = "8562414353:AAHH7aQQGRHGyMtBfbd77jvb_zVTckuYaM4"
CHAT_ID = "7701788482"

# 알림 임계값
ALERT_UP = 2.0           # 리포트용 상승 알림 (%)
ALERT_DOWN = -2.0        # 리포트용 하락 알림 (%)
EMERGENCY_DROP = -3.0    # 즉시 개별 알림을 보낼 급락 기준 (%)

# =========================
# 2. 유틸리티 함수
# =========================
def send_telegram(text, parse_mode="Markdown"):
    """텔레그램 메시지 전송 공통 함수"""
    url = f"https://api.telegram.org{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": parse_mode}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"전송 실패: {e}")

def get_color(change):
    if change is None: return "⚪"
    if change > 0: return "🔴"
    if change < 0: return "🔵"
    return "⚪"

def get_price_and_change(ticker):
    try:
        # 최근 5일 데이터를 가져와 전일 종가와 비교
        data = yf.Ticker(ticker).history(period="5d", auto_adjust=False)
        if data.empty or len(data) < 2:
            return None, None

        close_today = float(data["Close"].iloc[-1])
        close_prev = float(data["Close"].iloc[-2])

        if close_prev == 0: return close_today, None

        change_pct = ((close_today - close_prev) / close_prev) * 100
        return close_today, change_pct
    except Exception:
        return None, None

# =========================
# 3. 데이터 분석 및 저장소
# =========================
results = {"US": {"gain": [], "loss": []}, "KR": {"gain": [], "loss": []}}
all_positions = []
report_alerts = []

def analyze_ticker(name, ticker, market):
    price, change = get_price_and_change(ticker)
    if price is None: return

    color = get_color(change)
    symbol = "$" if market == "US" else "₩"
    price_fmt = f"{price:,.2f}" if market == "US" else f"{price:,.0f}"
    line = f"{color} {name}: {symbol}{price_fmt} ({change:+.2f}%)"

    # 1. 포트폴리오 분류
    target = results[market]["gain"] if change > 0 else results[market]["loss"]
    target.append((change, line, name, market))
    all_positions.append((change, line, name, market))

    # 2. 리포트용 알림 리스트 추가
    if change >= ALERT_UP:
        report_alerts.append(f"🚀 {market} {name}: {change:+.2f}%")
    elif change <= ALERT_DOWN:
        report_alerts.append(f"⚠️ {market} {name}: {change:+.2f}%")

    # 3. [핵심] -3% 이하 급락 시 즉시 개별 알림 전송
    if change <= EMERGENCY_DROP:
        emergency_msg = f"🚨 *[SUDDEN DROP ALERT]*\n\n" \
                        f"종목: *{name}* ({market})\n" \
                        f"현재가: {symbol}{price_fmt}\n" \
                        f"변동률: *{change:+.2f}%*\n\n" \
                        f"⚠️ 설정하신 하락 한계치({EMERGENCY_DROP}%)를 초과했습니다!"
        send_telegram(emergency_msg)

# =========================
# 4. 시장 및 포트폴리오 데이터 수집
# =========================
# 글로벌 지수
market_tickers = {"NASDAQ": "^IXIC", "S&P500": "^GSPC", "Bitcoin": "BTC-USD", "USD/KRW": "KRW=X"}
market_lines = []
for name, ticker in market_tickers.items():
    p, c = get_price_and_change(ticker)
    if p:
        color = get_color(c)
        market_lines.append(f"{color} {name}: {p:,.2f} ({c:+.2f}%)")

# 미국 포트폴리오
us_portfolio = ["JNJ", "AAPL", "MSFT", "SCHD", "QQQM", "JEPI", "GOOGL", "JEPQ", "IEF", "TLT"]
for t in us_portfolio: analyze_ticker(t, t, "US")

# 한국 포트폴리오
kr_portfolio = {
    "Samsung Electronics": "005930.KS", "KODEX S&P500": "379800.KS",
    "KOSEF 200TR": "294400.KS", "TIGER 은행고배당+": "307710.KS",
    "PLUS 고배당주": "161510.KS", "ACE KRX금현물": "411060.KS",
    "TIGER 미배당커버드콜": "458730.KS", "KIWOOM 국고채10년": "148070.KS",
    "RISE KIS국고채30년": "439870.KS"
}
for n, t in kr_portfolio.items(): analyze_ticker(n, t, "KR")

# =========================
# 5. 최종 리포트 메시지 구성
# =========================
all_sorted_up = sorted(all_positions, key=lambda x: x[0], reverse=True)
all_sorted_down = sorted(all_positions, key=lambda x: x[0])

msg = f"""*📊 Daily Market Report*

*🌎 Global Market*
{chr(10).join(market_lines)}

*🔥 Top Movers (Best 3)*
{chr(10).join([f"🚀 {n} ({m}): {c:+.2f}%" for c, _, n, m in all_sorted_up[:3]])}

*💧 Weakest Movers (Worst 3)*
{chr(10).join([f"💥 {n} ({m}): {c:+.2f}%" for c, _, n, m in all_sorted_down[:3]])}

*🇺🇸 US Portfolio*
{chr(10).join([l for _, l, _, _ in sorted(results["US"]["gain"], reverse=True)] or ["상승 없음"])}
{chr(10).join([l for _, l, _, _ in sorted(results["US"]["loss"])] or ["하락 없음"])}

*🇰🇷 KR Portfolio*
{chr(10).join([l for _, l, _, _ in sorted(results["KR"]["gain"], reverse=True)] or ["상승 없음"])}
{chr(10).join([l for _, l, _, _ in sorted(results["KR"]["loss"])] or ["하락 없음"])}

*🚨 Alerts (> 2% Move)*
{chr(10).join(report_alerts) if report_alerts else "특이사항 없음"}
"""

# 최종 전체 리포트 전송
send_telegram(msg)
