from flask import Flask, render_template, request, jsonify
import threading
import time
from binance.client import Client
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
import telegram

app = Flask(__name__)
bot = telegram.Bot(token=TELEGRAM_TOKEN)

client = Client()

alerts = []
prices = {}

def fetch_price_loop():
    while True:
        for alert in alerts:
            try:
                symbol = alert['symbol']
                target = float(alert['target'])
                price = float(client.futures_symbol_ticker(symbol=symbol)['price'])
                prices[symbol] = price
                direction = alert['direction']
                hit = (direction == 'up' and price >= target) or (direction == 'down' and price <= target)
                if not alert.get('triggered') and hit:
                    alert['triggered'] = True
                    message = f"🚨 {symbol}: Цель {target} {'достигнута 🔼' if direction == 'up' else 'пробита 🔽'}\nТекущая цена: {price}\nЗаметка: {alert['note']}"
                    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
            except Exception as e:
                print(f"[ERR] {e}")
        time.sleep(5)

@app.route('/')
def index():
    return render_template('index.html', alerts=alerts, prices=prices)

@app.route('/add_alert', methods=['POST'])
def add_alert():
    data = request.get_json()
    alerts.append({
        'symbol': data['symbol'],
        'target': float(data['target']),
        'direction': data['direction'],
        'note': data['note'],
        'triggered': False
    })
    return jsonify({'success': True})

@app.route('/delete_alert', methods=['POST'])
def delete_alert():
    data = request.get_json()
    index = data.get('index')
    if index is not None and 0 <= index < len(alerts):
        alerts.pop(index)
    return jsonify({'success': True})

@app.route('/get_prices')
def get_prices():
    return jsonify(prices)

if __name__ == '__main__':
    t = threading.Thread(target=fetch_price_loop)
    t.daemon = True
    t.start()
    app.run(debug=True, host="0.0.0.0", port=10000)
