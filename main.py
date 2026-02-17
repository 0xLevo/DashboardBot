import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone, timedelta
import json 
import base64

# --- ANALİZ EDİLECEK COINLER (Uzun Vadeli Model) ---
TOP_COINS = ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'LINK', 'BNB', 'ADA', 'AVAX']

def get_rainbow_bands(prices, dates):
    try:
        y = np.log(prices)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)
        
        # --- 2050 YILINA KADAR PROJEKSİYON ---
        target_year = 2050
        last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
        future_days = (datetime(target_year, 1, 1) - last_date).days
        
        # Eğer tarih zaten 2050'yi geçtiyse limit koy
        if future_days < 0: future_days = 365 

        future_x = np.arange(len(y) + future_days)
        
        # Regresyon çizgisi (2050'ye uzatılmış)
        regression_line = slope * future_x + intercept
        
        # Standart Sapma
        residuals = y - (slope * x + intercept)
        std_dev = np.std(residuals)
        
        # --- BANTLARIN 2050'YE UZATILMASI ---
        bands = {
            "bubble": np.exp(regression_line + 2.5 * std_dev).tolist(),
            "fomo": np.exp(regression_line + 1.5 * std_dev).tolist(),
            "neutral": np.exp(regression_line).tolist(),
            "buy": np.exp(regression_line - 1.0 * std_dev).tolist(),
            "firesale": np.exp(regression_line - 2.0 * std_dev).tolist(),
        }
        
        # Gelecekteki tarihleri oluştur
        future_dates = [ (last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(future_days) ]
        all_dates = dates + future_dates
            
        return bands, all_dates
    except: return None, dates

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []
    
    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            # MEXC'den alınabilecek maksimum veri (yaklaşık 3-4 yıl)
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=1000)
            if len(bars) < 100: continue
            
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            prices = df['close'].tolist()
            dates = pd.to_datetime(df['time'], unit='ms').dt.strftime('%Y-%m-%d').tolist()
            
            bands, all_dates = get_rainbow_bands(prices, dates)

            if bands:
                results.append({
                    'symbol': symbol,
                    'price': f"{prices[-1]:.6g}",
                    'dates': all_dates,
                    'prices': prices, # Fiyat geçmiş veridir
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
        <title>Crypto Rainbow Dashboard 2050</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
            <h1 class="text-3xl font-bold text-white">Rainbow <span class="text-sky-400">Dashboard 2050</span></h1>
            <span class="text-sm text-slate-400 font-mono">{full_update} UTC</span>
        </header>

        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
    """

    for i in data:
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        html += f"""
        <div class="card p-5 cursor-pointer" onclick="showModal('{encoded_data}')">
            <div class="flex justify-between items-center mb-3">
                <span class="text-lg font-bold text-white font-mono">{i['symbol']}</span>
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
                document.getElementById('m-title').innerText = data.symbol + " Rainbow Model to 2050";
                document.getElementById('modal').classList.remove('hidden');

                if (currentChart) currentChart.destroy();

                const ctx = document.getElementById('coinChart').getContext('2d');
                currentChart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.dates,
                        datasets: [
                            { label: 'Price', data: data.prices, borderColor: '#fff', borderWidth: 2, fill: false, tension: 0.1, yAxisID: 'y', order: 1 },
                            { label: 'Bubble', data: data.bands.bubble, borderColor: '#ef4444', borderWidth: 1, fill: false, tension: 0.1, yAxisID: 'y' },
                            { label: 'FOMO', data: data.bands.fomo, borderColor: '#f97316', borderWidth: 1, fill: false, tension: 0.1, yAxisID: 'y' },
                            { label: 'Neutral', data: data.bands.neutral, borderColor: '#eab308', borderWidth: 1, fill: false, tension: 0.1, yAxisID: 'y' },
                            { label: 'Buy', data: data.bands.buy, borderColor: '#22c55e', borderWidth: 1, fill: false, tension: 0.1, yAxisID: 'y' },
                            { label: 'Fire Sale', data: data.bands.firesale, borderColor: '#166534', borderWidth: 1, fill: false, tension: 0.1, yAxisID: 'y' }
                        ]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: { y: { type: 'logarithmic', grid: { color: '#334155' } }, x: { grid: { color: '#334155' } } },
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
