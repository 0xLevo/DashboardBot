import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json 
import base64

# --- TOP COINS ---
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX', 
    'LINK', 'MATIC', 'TON', 'SHIB', 'LTC', 'BCH', 'ATOM', 'UNI', 'NEAR', 'INJ'
] # Test amaçlı kısa liste, 100 yapabilirsiniz.

def get_log_regression_status(prices):
    try:
        y = np.log(prices)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        expected_log_price = slope * x[-1] + intercept
        current_log_price = y[-1]
        diff = current_log_price - expected_log_price
        
        if diff < -0.4: return "BUY", "#22c55e"
        elif diff > 0.4: return "BUBBLE", "#ef4444"
        else: return "NEUTRAL", "#64748b"
    except: return "UNKNOWN", "#333"

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []
    
    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            # 1 günlük 200 adet veri -> Grafik için yeterli
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=200)
            if len(bars) < 100: continue
            
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            prices = df['close'].tolist()
            curr_price = prices[-1]
            dates = pd.to_datetime(df['time'], unit='ms').dt.strftime('%Y-%m-%d').tolist()
            
            status, color = get_log_regression_status(prices)

            results.append({
                'symbol': symbol,
                'price': f"{curr_price:.6g}",
                'status': status,
                'color': color,
                'dates': dates,
                'prices': prices,
                'details': {
                    "Current Price": f"{curr_price:.6g} USDT",
                    "Trend": status,
                    "Days": "200"
                }
            })
            time.sleep(0.05)
        except: continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    # Tüm verileri JSON olarak gömüyoruz
    data_json = json.dumps(data)
    
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Crypto Regression Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Poppins', sans-serif; background-color: #0f172a; color: white; }}
            .card {{ background: #1e293b; border-radius: 16px; transition: 0.3s; }}
            .card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }}
            .modal {{ backdrop-filter: blur(5px); }}
        </style>
    </head>
    <body class="p-6">
        <header class="flex justify-between items-center pb-8 border-b border-slate-700 mb-8">
            <h1 class="text-3xl font-bold text-white">Market Regression <span class="text-sky-400">Dashboard</span></h1>
            <span class="text-sm text-slate-400 font-mono">{full_update} UTC</span>
        </header>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4" id="coin-grid">
    """

    for i in data:
        # Tıklanabilir veri için veriyi base64 ile kodluyoruz
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        html += f"""
        <div class="card p-5 cursor-pointer" onclick="showModal('{encoded_data}')" style="border-left: 4px solid {i['color']};">
            <div class="flex justify-between items-center mb-3">
                <span class="text-lg font-bold text-white font-mono">{i['symbol']}</span>
                <span class="text-xs font-semibold px-2 py-1 rounded-md" style="background: {i['color']}30; color: {i['color']};">
                    {i['status']}
                </span>
            </div>
            <div class="text-2xl font-extrabold text-white mb-1">${i['price']}</div>
        </div>
        """

    html += """
        </div>

        <div id="modal" class="modal fixed inset-0 bg-black/70 hidden flex items-center justify-center p-4">
            <div class="bg-slate-800 p-6 rounded-2xl max-w-2xl w-full">
                <div class="flex justify-between mb-4">
                    <h2 id="m-title" class="text-2xl font-bold"></h2>
                    <button onclick="closeModal()" class="text-2xl">&times;</button>
                </div>
                <canvas id="coinChart" height="150"></canvas>
            </div>
        </div>

        <script>
            let currentChart = null;

            function showModal(encodedData) {
                const data = JSON.parse(atob(encodedData));
                document.getElementById('m-title').innerText = data.symbol + " Log Regression";
                document.getElementById('modal').classList.remove('hidden');

                if (currentChart) currentChart.destroy();

                const ctx = document.getElementById('coinChart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.dates,
                        datasets: [{
                            label: 'Price',
                            data: data.prices,
                            borderColor: '#38bdf8',
                            borderWidth: 2,
                            fill: false,
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: { y: { type: 'logarithmic' } },
                        plugins: { legend: { labels: { color: 'white' } } }
                    }
                });
            }

            function closeModal() { document.getElementById('modal').classList.add('hidden'); }
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    create_html(analyze_market())
