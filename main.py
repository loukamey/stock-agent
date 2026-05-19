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

WATCHLIST = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META", "AMD"]

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
                    "high": quote.get("03. high", "N/A"),
                    "low": quote.get("04. low", "N/A"),
                })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    return stocks

def check_urgent(stocks):
    urgent = []
    for stock in stocks:
        change = abs(stock.get("change_float", 0))
        if change >= 5:
            direction = "📈 SURGED" if stock["change_float"] > 0 else "📉 CRASHED"
            urgent.append(f"{stock['symbol']} {direction} {stock['change']} to ${stock['price']}")
    return urgent

def generate_report(stocks):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are Louka's personal stock market advisor. Louka is 13, lives in Dubai, has 9,000 AED total. MAX 2,000 AED into stocks. Parents help with buying.

Today: {datetime.now().strftime("%B %d, %Y")}
Stock data: {json.dumps(stocks, indent=2)}

Write his daily brief in this EXACT bullet point format:

Hey Louka 👋 Here's your brief for today:

🎯 TOP PICK TODAY
- [Stock] at $[price] — [2-3 sentences why]
- Suggested amount: [X] AED

💰 YOUR MOVES TODAY
- [X] AED → [Stock] — [one line reason]
- [X] AED → [Stock] — [one line reason]
- Keep the rest as cash

🚫 AVOID TODAY
- [Stock] — [one line reason]

⚠️ WATCH OUT
- [One specific risk today]

👀 TOMORROW
- [One thing to watch]

Total suggested today: MAX 300-500 AED."""

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
        alert = "🚨🚨🚨 <b>URGENT STOCK ALERT</b> 🚨🚨🚨\n\nLouka, big market move happening NOW!\n\n"
        for u in urgent:
            alert += f"⚡ {u}\n"
        alert += f"\nThis could be a buying or selling opportunity!\nShow your parents immediately!\n\n⏰ {datetime.now().strftime('%H:%M Dubai time')}"
        send_telegram(alert)
        print(f"URGENT ALERT SENT")

def daily_job():
    print(f"Running stock scan - {datetime.now()}")
    stocks = get_stock_data()
    print(f"Got {len(stocks)} stocks")
    report = generate_report(stocks)
    message = f"📈 <b>Your Daily Stock Brief - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}"
    send_telegram(message)

print("Stock Intelligence Agent is running!")
print(f"Started at: {datetime.now()}")
daily_job()

schedule.every().day.at("05:00").do(daily_job)
schedule.every(1).hours.do(hourly_check)

while True:
    schedule.run_pending()
    time.sleep(60)
