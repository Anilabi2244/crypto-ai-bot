import os
import telebot
import time
from groq import Groq
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Web Server ---
app = Flask('')
@app.route('/')
def home(): return "Buddy Pro is LIVE! 🚀"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

# --- Configuration ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
MY_CHAT_ID = os.getenv('MY_CHAT_ID') 

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

# --- Market Monitoring Logic ---
def get_market_alerts():
    try:
        tickers = binance_client.ticker_24hr()
        # High volume/hype coins ni check chesthunnam
        top_vol = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)[:5]
        alerts = []
        for coin in top_vol:
            symbol = coin['symbol']
            if not symbol.endswith('USDT'): continue
            klines = binance_client.klines(symbol, "1h", limit=30)
            df = pd.DataFrame(klines, columns=['t','o','h','l','c','v','ct','qv','nt','tb','tq','i'])
            df['close'] = df['close'].astype(float)
            rsi = ta.rsi(df['close'], length=14).iloc[-1]
            
            if rsi < 32: # Oversold / Buy Alert
                alerts.append(f"🚨 {symbol} oversold zone lo undi (RSI: {rsi:.2f}). Check chey buddy!")
        return alerts
    except Exception as e:
        return []

def auto_alert_loop():
    while True:
        if MY_CHAT_ID:
            signals = get_market_alerts()
            for s in signals:
                bot.send_message(MY_CHAT_ID, s)
        time.sleep(600) # Every 10 mins ki scan chesthundi

# --- Data Logic for Portfolio ---
def get_real_data():
    try:
        account = binance_client.account()
        # Nuvvu pampina LINK, ETH, HBAR balances correct ga pick chesthundhi
        balances = [f"{b['asset']}: {b['free']}" for b in account['balances'] if float(b['free']) > 0]
        orders = binance_client.get_open_orders()
        formatted_orders = [f"{o['symbol']} @ {o['price']} ({o['side']})" for o in orders]
        return f"Portfolio: {balances} | Open Orders: {formatted_orders}"
    except Exception as e:
        return "Live data access avvaledu buddy."

# --- Natural Buddy Chat ---
@bot.message_handler(func=lambda message: True)
def buddy_chat(message):
    live_info = get_real_data()
    system_prompt = (
        "You are Buddy, a chill human-like crypto expert. "
        "FORBIDDEN: 'Pukka', 'Chal', 'Vinnu', 'Chudu' (ending sentences). "
        "Talk like a best friend in English script only. Use simple Tanglish. "
        f"Use this Real Data: {live_info}. Be natural, witty and helpful."
    )
    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message.text}],
            temperature=0.4
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Buddy, AI chinna glitch lo undi. Malli try chey.")

if __name__ == "__main__":
    Thread(target=run_web).start()
    Thread(target=auto_alert_loop).start() # Background monitoring started
    bot.polling(none_stop=True)
