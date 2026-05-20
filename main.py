import requests
import schedule
import time
from datetime import datetime
import json
import os
import anthropic

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
ALPHA_VANTAGE_KEY = "DCJ6C7AGRNGWMXQO"
TELEGRAM_TOKEN = "8370691561:AAGt5T8XrIRKZOBeI322Jiugk9jw_SKOEjk"
TELEGRAM_CHAT_ID = "8526660731"

WATCHLIST = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD", "EMIRATESNBD.DU", "EMAAR.DU", "ADNOCDIST.AD", "FAB.AD", "ALDAR.AD"]

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"}
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            print("Telegram message sent!")
        else:
            print(f"Telegram error: {response.text}")
    except Exception as e:
        print(f"Telegram error: {e}")

def get_stock_data():
    stocks = []
    for symbol in WATCHLIST:
        try:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
            response = requests.get(url, timeout=10)
            data = response.json()
            quote = data.get("Global Quote", {})
            if quote:
                change = quote.get("10. change percent", "0%").replace("%", "")
                stocks.append({
                    "symbol": symbol,
                    "price": quote.get("05. price", "N/A"),
                    "change": quote.get("10. change percent", "N/A"),
                    "change_float": float(change) if change else 0,
                })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    return stocks

def check_urgent(stocks):
    urgent = []
    for stock in stocks:
        change = abs(stock.get("change_float", 0))
        if change >= 8:
            direction = "surged" if stock["change_float"] > 0 else "crashed"
            urgent.append(f"{stock['symbol']} {direction} {stock['change']} to ${stock['price']}")
    return urgent

def generate_report(stocks):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are Louka's personal stock advisor. 13 years old, Dubai, MAX 2,000 AED in stocks, parents help buy.

Today: {datetime.now().strftime("%B %d, %Y")}
Stocks: {json.dumps(stocks, indent=2)}

Hey Louka 👋 Here's your brief for today:

🎯 TOP PICK TODAY
- [Stock] at $[price] — [2-3 sentences why]
- Suggested: [X] AED

💰 YOUR MOVES TODAY
- [X] AED → [Stock] — [reason]
- [X] AED → [Stock] — [reason]
- Keep rest as cash

🚫 AVOID TODAY
- [Stock] — [reason]

⚠️ WATCH OUT
- [One risk]

👀 TOMORROW
- [One thing to watch]

Max 300-500 AED total today."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def hourly_check():
    print(f"Hourly stock check - {datetime.now()}")
    stocks = get_stock_data()
    urgent = check_urgent(stocks)
    if urgent:
        reason = urgent[0]
        alert = f"🚨‼️\n\n<b>LOUKA — ACT NOW</b>\n\n{reason}\n\n→ Check your broker app immediately\n\n⏰ {datetime.now().strftime('%H:%M')} Dubai time"
        send_telegram(alert)
        print("URGENT STOCK ALERT SENT")

def daily_job():
    print(f"Running stock scan - {datetime.now()}")
    stocks = get_stock_data()
    report = generate_report(stocks)
    message = f"📈 <b>Your Daily Stock Brief - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}"
    send_telegram(message)

print("Stock Agent running!")
print(f"Started: {datetime.now()}")
daily_job()

schedule.every().day.at("05:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
