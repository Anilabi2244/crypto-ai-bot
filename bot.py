import os
import telebot
from groq import Groq
from binance.spot import Spot as Client
import pandas as pd
from flask import Flask
from threading import Thread

# --- Web Server ---
app = Flask('')
@app.route('/')
def home(): return "Alpha Hunter Pro is LIVE! 🚀"

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

# --- Data Fetching Logic ---

def get_real_portfolio():
    try:
        account = binance_client.account()
        # Filtering balances that actually have coins
        balances = [f"{b['asset']}: {b['free']}" for b in account['balances'] if float(b['free']) > 0 or float(b['locked']) > 0]
        return ", ".join(balances) if balances else "No coins found."
    except Exception as e:
        return f"Error: {str(e)}"

def get_real_orders():
    try:
        orders = binance_client.get_open_orders()
        if not orders: return "No open orders."
        formatted = [f"{o['symbol']} @ {o['price']} (Type: {o['side']})" for o in orders]
        return ", ".join(formatted)
    except Exception as e:
        return f"Error: {str(e)}"

# --- Natural Buddy Chat ---

@bot.message_handler(func=lambda message: True)
def buddy_chat(message):
    user_msg = message.text.lower()
    
    # Live Data Sync
    portfolio = get_real_portfolio()
    orders = get_real_orders()
    
    # System Instruction for strict Tanglish & Accuracy
    system_prompt = (
        "You are Buddy, a chill crypto expert peer. NEVER hallucinate data. "
        "Use this REAL DATA to answer: "
        f"Portfolio: [{portfolio}] | Open Orders: [{orders}]. "
        "Respond ONLY in Tanglish (Telugu words in English script). "
        "Strictly avoid Telugu alphabet. Be a close friend, use words like 'Buddy', 'Chudu', 'Pukka'."
    )

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message.text}
            ],
            temperature=0.3 # Accuracy kosam low temperature
        )
        bot.reply_to(message, completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Buddy, AI lo glitch. Try again!")

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot.polling(none_stop=True)
