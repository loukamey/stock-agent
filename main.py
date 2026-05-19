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

WATCHLIST = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "GOOGL", "META"]

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
                stocks.append({
                    "symbol": symbol,
                    "price": quote.get("05. price", "N/A"),
                    "change": quote.get("10. change percent", "N/A"),
                    "high": quote.get("03. high", "N/A"),
                    "low": quote.get("04. low", "N/A"),
                })
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
    return stocks

def generate_report(stocks):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    prompt = f"""You are a professional stock market analyst.
Today: {datetime.now().strftime("%B %d, %Y")}

STOCK DATA:
{json.dumps(stocks, indent=2)}

Write a sharp daily stock briefing for a young investor with small budget covering:
- Best and worst performers today
- Top 3 investment suggestions under 500 AED each
- One stock pick of the day with clear reasoning
- Any risks to watch

Keep it under 3500 characters for Telegram. Be specific with prices."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

def daily_job():
    print(f"Running stock scan - {datetime.now()}")
    stocks = get_stock_data()
    print(f"Got {len(stocks)} stocks")
    report = generate_report(stocks)
    message = f"📈 <b>Daily Stock Report - {datetime.now().strftime('%B %d, %Y')}</b>\n\n{report}"
    send_telegram(message)

print("Stock Intelligence Agent is running!")
print(f"Started at: {datetime.now()}")
print("Sending test report now...")
daily_job()

schedule.every().day.at("05:00").do(daily_job)

while True:
    schedule.run_pending()
    time.sleep(60)
