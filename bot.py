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
def home(): return "Buddy Pro Agent is LIVE! 🚀"

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

# --- Real Data Logic (Clean & Accurate) ---
def get_clean_portfolio():
    try:
        account = binance_client.account()
        # Filter balances and format properly
        data = []
        for b in account['balances']:
            free = float(b['free'])
            locked = float(b['locked'])
            total = free + locked
            if total > 0.00001: # Small dust coins ni ignore chesthunnam
                data.append(f"{b['asset']}: {total:.4f}")
        return ", ".join(data) if data else "Portfolio empty buddy."
    except Exception as e:
        return f"Data error: {str(e)}"

def get_clean_orders():
    try:
        orders = binance_client.get_open_orders()
        if not orders: return "No open orders."
        res = [f"{o['symbol']} {o['side']} @ {o['price']}" for o in orders]
        return ", ".join(res)
    except Exception as e:
        return f"Order error: {str(e)}"

# --- Automatic Alert Loop ---
def auto_alert_loop():
    while True:
        if MY_CHAT_ID:
            try:
                # RSI Analysis for top volume coins
                tickers = binance_client.ticker_24hr()
                top_vol = sorted(tickers, key=lambda x: float(x['quoteVolume']), reverse=True)[:5]
                for coin in top_vol:
                    sym = coin['symbol']
                    if not sym.endswith('USDT'): continue
                    k = binance_client.klines(sym, "1h", limit=30)
                    close = pd.Series([float(x[4]) for x in k])
                    rsi = ta.rsi(close, length=14).iloc[-1]
                    if rsi < 30:
                        bot.send_message(MY_CHAT_ID, f"🚀 Buddy, {sym} oversold lo undi! Entry chudu. RSI: {rsi:.2f}")
            except: pass
        time.sleep(900) # Every 15 mins

# --- Natural Buddy Chat ---
@bot.message_handler(func=lambda message: True)
def buddy_chat(message):
    p_data = get_clean_portfolio()
    o_data = get_clean_orders()
    
    # Precise instructions to avoid bad words and hallucination
    system_prompt = (
        "You are Buddy, a human-like crypto expert. Talk like a real friend. "
        "FORBIDDEN: 'Pukka', 'Chal', 'Vinnu'. Use only English script. "
        f"REAL DATA: Portfolio is {p_data}. Open Orders are {o_data}. "
        "Strictly use this real data. If asked about suggestions, be direct in Tanglish. "
        "Example: 'Hey buddy, nee daggara LINK bagundi, but ETH konchem thakkuva undi.'"
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": message.text}],
            temperature=0.4
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Buddy, AI lo chinna disturbance. Malli adugu!")

if __name__ == "__main__":
    Thread(target=run_web).start()
    Thread(target=auto_alert_loop).start()
    bot.polling(none_stop=True)
