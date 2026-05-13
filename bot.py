import os
import telebot
import google.generativeai as genai
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Dummy Web Server for Render ---
app = Flask('')
@app.route('/')
def home():
    return "AI Bot is Alive!"

def run_web():
    app.run(host='0.0.0.0', port=10000)

# --- Config ---
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)

# UPDATED MODEL NAME HERE
model = genai.GenerativeModel('gemini-pro') 

binance_client = Client(BINANCE_API_KEY, BINANCE_SECRET_KEY)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste Buddy! Eesari bot pakka working. Market analysis kosam /analysis ani type chey.")

@bot.message_handler(commands=['analysis'])
def get_analysis(message):
    try:
        symbol = "BTCUSDT"
        klines = binance_client.klines(symbol, "1h", limit=100)
        df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
        df['close'] = df['close'].astype(float)
        df['RSI'] = ta.rsi(df['close'], length=14)
        
        price = df['close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        advice = "HOLD"
        if rsi < 30: advice = "BUY (Oversold)"
        elif rsi > 70: advice = "SELL (Overbought)"
        
        response = f"📊 *{symbol} Analysis*\n\nPrice: ${price}\nRSI: {rsi:.2f}\nAction: {advice}"
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    try:
        response = model.generate_content(f"User says: {message.text}. Respond as a friendly crypto expert in Telugu and English mix.")
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, "Gemini AI busy ga undi, kani nenu unnaga! Analysis kosam /analysis kottu.")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    print("Bot is starting...")
    bot.polling(none_stop=True)
