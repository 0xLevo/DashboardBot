import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json 
import base64

# --- TOP 100 COINS (Güncellenmiş Liste) ---
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX', 
    'LINK', 'MATIC', 'TON', 'SHIB', 'LTC', 'BCH', 'ATOM', 'UNI', 'NEAR', 'INJ', 
    'OP', 'ICP', 'FIL', 'LDO', 'TIA', 'STX', 'APT', 'ARB', 'RNDR', 'VET', 
    'KAS', 'ETC', 'ALGO', 'RUNE', 'EGLD', 'SEI', 'SUI', 'AAVE', 'FTM', 'SAND',
    'IMX', 'MANA', 'GRT', 'FLOW', 'GALA', 'DYDX', 'QNT', 'MKR', 'WLD'
]

def get_rainbow_bands(prices):
    """
    Logaritmik regresyon kullanarak rainbow bantlarını hesaplar.
    Daha doğru bir model için standart sapmalar optimize edilmiştir.
    """
    try:
        y = np.log(prices)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        
        # Temel Regresyon Çizgisi
        regression_line = slope * x + intercept
        
        # Standart Sapma Hesaplama
        residuals = y - regression_line
        std_dev = np.std(residuals)
        
        # --- BANT HESAPLAMALARI (Daha doğru renk dağılımı) ---
        bands = {
            "bubble": np.exp(regression_line + 2.5 * std_dev).tolist(),
            "fomo": np.exp(regression_line + 1.5 * std_dev).tolist(),
            "neutral": np.exp(regression_line).tolist(),
            "buy": np.exp(regression_line - 1.0 * std_dev).tolist(),
            "firesale": np.exp(regression_line - 2.0 * std_dev).tolist(),
        }
        
        # Güncel fiyatın hangi bantta olduğunu belirle
        curr_price = prices[-1]
        if curr_price > bands["bubble"][-1]: status = ("BUBBLE", "#ef4444")
        elif curr_price > bands["fomo"][-1]: status = ("FOMO", "#f97316")
        elif curr_price > bands["neutral"][-1]: status = ("NEUTRAL", "#eab308")
        elif curr_price > bands["buy"][-1]: status = ("BUY", "#22c55e")
        else: status = ("FIRE SALE", "#166534")
            
        return bands, status
    except: return None, ("UNKNOWN", "#333")

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []
    
    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            # 500 günlük veri -> Daha uzun vadeli trend için
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=500)
            if len(bars) < 200: continue
            
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            prices = df['close'].tolist()
            dates = pd.to_datetime(df['time'], unit='ms').dt.strftime('%Y-%m-%d').tolist()
            
            bands, status = get_rainbow_bands(prices)

            if bands:
                results.append({
                    'symbol': symbol,
                    'price': f"{prices[-1]:.6g}",
                    'status': status[0],
                    'color': status[1],
                    'dates': dates,
                    'prices': prices,
                    'bands': bands
                })
            time.sleep(0.05)
        except: continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Crypto Rainbow Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels"></script>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Poppins', sans-serif; background-color: #0f172a; color: white; }}
            .card {{ background: #1e293b; border-radius: 16px; transition: 0.3s; }}
            .card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }}
            .modal-content {{ background: #1e293b; width: 95vw; height: 90vh; }}
        </style>
    </head>
    <body class="p-6">
        <header class="flex justify-between items-center pb-8 border-b border-slate-700 mb-8">
            <h1 class="text-3xl font-bold text-white">Rainbow <span class="text-sky-400">Dashboard</span></h1>
            <span class="text-sm text-slate-400 font-mono">{full_update} UTC</span>
        </header>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
    """

    for i in data:
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

        <div id="modal" class="fixed inset-0 bg-black/80 hidden flex items-center justify-center p-4">
            <div class="modal-content p-6 rounded-3xl flex flex-col">
                <div class="flex justify-between mb-4">
                    <h2 id="m-title" class="text-3xl font-bold"></h2>
                    <button onclick="closeModal()" class="text-4xl">&times;</button>
                </div>
                <div class="flex-grow">
                    <canvas id="coinChart"></canvas>
                </div>
            </div>
        </div>

        <script>
            let currentChart = null;

            function showModal(encodedData) {
                const data = JSON.parse(atob(encodedData));
                document.getElementById('m-title').innerText = data.symbol + " Rainbow Model";
                document.getElementById('modal').classList.remove('hidden');

                if (currentChart) currentChart.destroy();

                const ctx = document.getElementById('coinChart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.dates,
                        datasets: [
                            { label: 'Price', data: data.prices, borderColor: '#fff', borderWidth: 3, fill: false, tension: 0.1, yAxisID: 'y', order: 1 },
                            { label: 'Bubble', data: data.bands.bubble, borderColor: '#ef4444', backgroundColor: '#ef444430', borderWidth: 1, fill: '-1', tension: 0.1, yAxisID: 'y' },
                            { label: 'FOMO', data: data.bands.fomo, borderColor: '#f97316', backgroundColor: '#f9731630', borderWidth: 1, fill: '-1', tension: 0.1, yAxisID: 'y' },
                            { label: 'Neutral', data: data.bands.neutral, borderColor: '#eab308', backgroundColor: '#eab30830', borderWidth: 1, fill: '-1', tension: 0.1, yAxisID: 'y' },
                            { label: 'Buy', data: data.bands.buy, borderColor: '#22c55e', backgroundColor: '#22c55e30', borderWidth: 1, fill: '-1', tension: 0.1, yAxisID: 'y' },
                            { label: 'Fire Sale', data: data.bands.firesale, borderColor: '#166534', backgroundColor: '#16653430', borderWidth: 1, fill: false, tension: 0.1, yAxisID: 'y' }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { y: { type: 'logarithmic', grid: { color: '#334155' } }, x: { grid: { color: '#334155' } } },
                        plugins: {
                            legend: { labels: { color: 'white' } }
                        }
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
