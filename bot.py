import os
import telebot
from groq import Groq
from binance.spot import Spot as Client
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread

# --- Web Server for Render ---
app = Flask('')
@app.route('/')
def home():
    return "Groq AI Bot is Alive!"

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Namaste Buddy! Groq AI Agent ready. /analysis kottu leda natho chat chey.")

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
        if rsi < 35: advice = "BUY (Oversold)"
        elif rsi > 65: advice = "SELL (Overbought)"
        
        response = f"📊 *{symbol} Analysis*\n\nPrice: ${price}\nRSI: {rsi:.2f}\nAction: {advice}"
        bot.reply_to(message, response, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"Error: {str(e)}")

@bot.message_handler(func=lambda message: True)
def chat_with_groq(message):
    try:
        chat_completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a crypto trading expert. Respond in a mix of Telugu and English. Keep it friendly and helpful."},
                {"role": "user", "content": message.text}
            ],
            model="llama3-8b-8192",
        )
        bot.reply_to(message, chat_completion.choices[0].message.content)
    except Exception as e:
        bot.reply_to(message, "Groq lo chinna error vachindi buddy, kani analysis pani chestundi. /analysis try chey.")

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.start()
    bot.polling(none_stop=True)
