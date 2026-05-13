import os
import time
import telebot
import google.generativeai as genai
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta

# --- Config ---
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
    bot.reply_to(message, "Namaste! I am your AI Crypto Agent. Use /analysis or just chat with me!")

@bot.message_handler(commands=['analysis'])
def analysis(message):
    res = get_market_analysis()
    bot.reply_to(message, res)

@bot.message_handler(func=lambda message: True)
def chat(message):
    prompt = f"User: {message.text}. Respond like a friendly crypto expert in a mix of Telugu and English."
    response = model.generate_content(prompt)
    bot.reply_to(message, response.text)

if __name__ == "__main__":
    bot.polling(none_stop=True)
