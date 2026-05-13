import os
import telebot
from groq import Groq
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Web Server ---
app = Flask('')
@app.route('/')
def home(): return "Crypto AI Agent is Online!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Config ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

# --- Functions for AI to use ---

def get_binance_account_details():
    try:
        account = binance_client.account()
        balances = [b for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
        return str(balances)
    except Exception as e:
        return f"Error fetching account: {str(e)}"

def get_open_orders():
    try:
        orders = binance_client.get_open_orders()
        if not orders: return "No open orders right now buddy."
        return str(orders)
    except Exception as e:
        return f"Error fetching orders: {str(e)}"

# --- Telegram Logic ---

@bot.message_handler(commands=['start', 'analysis'])
def handle_commands(message):
    if message.text == '/start':
        bot.reply_to(message, "Namaste Buddy! Groq AI ready. Ask me to check orders or portfolio.")
    else:
        # Standard Technical Analysis
        klines = binance_client.klines("BTCUSDT", "1h", limit=50)
        price = float(klines[-1][4])
        bot.reply_to(message, f"📊 BTC Price: ${price:,.2f}\nAction: Use chat for detailed analysis.")

@bot.message_handler(func=lambda message: True)
def smart_chat(message):
    user_msg = message.text.lower()
    
    # Context Injection: Manam AI ki actual Binance data ni "System Message" lo pampisthunnam
    data_context = ""
    if "order" in user_msg or "trade" in user_msg:
        data_context = f"\n[LIVE DATA: Open Orders: {get_open_orders()}]"
    elif "portfolio" in user_msg or "balance" in user_msg:
        data_context = f"\n[LIVE DATA: Account Balance: {get_binance_account_details()}]"

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "system", 
                    "content": f"You are a helpful crypto expert. Use the provided LIVE DATA to answer. If no data is provided, talk generally. Respond in Tanglish (English script). Be direct, no definitions.{data_context}"
                },
                {"role": "user", "content": message.text}
            ],
            temperature=0.2, # Accuracy kosam temperature taggincha
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Buddy, Groq lo error. Try again later.")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    bot.polling(none_stop=True)
