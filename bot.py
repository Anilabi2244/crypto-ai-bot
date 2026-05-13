import os
import time
import telebot
import google.generativeai as genai
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Dummy Web Server for Render Free Tier ---
app = Flask('')
@app.route('/')
def home():
    return "AI Bot is Alive!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# --- Original Bot Config ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

def get_market_analysis(symbol="BTCUSDT"):
    try:
        klines = binance_client.klines(symbol, "1h", limit=100)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['RSI'] = ta.rsi(df['close'], length=14)
        price = df['close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        advice = "HOLD"
        if rsi < 30: advice = "BUY (Oversold)"
        elif rsi > 70: advice = "SELL (Overbought)"
        return f"Price: ${price}\nRSI: {rsi:.2f}\nAction: {advice}"
    except Exception as e:
        return f"Error: {str(e)}"

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Namaste! AI Bot is running on Free Tier now. Use /analysis.")

@bot.message_handler(func=lambda message: True)
def chat(message):
    response = model.generate_content(f"User: {message.text}. Respond as a crypto friend in Telugu/English.")
    bot.reply_to(message, response.text)

if __name__ == "__main__":
    # Web server ni separate thread lo start chestunnam
    t = Thread(target=run_web)
    t.start()
    print("Bot is running...")
    bot.polling(none_stop=True)
