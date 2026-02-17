import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone, timedelta
import json
import base64

# --- TOP 100+ COIN LISTESİ (Stabil Coinler Hariç) ---
# CMC verilerine göre kapsamlı liste
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX',
    'LINK', 'MATIC', 'TON', 'SHIB', 'LTC', 'BCH', 'ATOM', 'UNI', 'NEAR', 'INJ',
    'OP', 'ICP', 'FIL', 'LDO', 'TIA', 'STX', 'APT', 'ARB', 'RNDR', 'VET',
    'KAS', 'ETC', 'ALGO', 'RUNE', 'EGLD', 'SEI', 'SUI', 'AAVE', 'FTM', 'SAND',
    'IMX', 'MANA', 'GRT', 'FLOW', 'GALA', 'DYDX', 'QNT', 'MKR', 'WLD', 'APE',
    'SNX', 'INJ', 'AXS', 'CHZ', 'MANA', 'SAND', 'LUNC', 'PEPE', 'BONK', 'ORDI'
]

def get_projections(prices, dates):
    """Logaritmik regresyon ile geçmiş ve gelecek bantlarını hesaplar."""
    try:
        y = np.log(prices)
        x = np.arange(len(y))
        slope, intercept = np.polyfit(x, y, 1)

        # 2050'ye kadar projeksiyon
        last_date = datetime.strptime(dates[-1], '%Y-%m-%d')
        future_days = (datetime(2050, 1, 1) - last_date).days
        if future_days < 0: future_days = 365

        future_x = np.arange(len(y) + future_days)
        regression_line = slope * future_x + intercept
        
        # Standart Sapma
        residuals = y - (slope * x + intercept)
        std_dev = np.std(residuals)

        # Bantları Hesapla (TradingView formatına uygun)
        future_dates = [ (last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(future_days) ]
        all_dates = dates + future_dates
        
        # Regresyon çizgisi verisi
        line_data = []
        for i in range(len(all_dates)):
            line_data.append({'time': all_dates[i], 'value': np.exp(regression_line[i])})

        # Bant verileri
        bands = {
            "top": [{'time': all_dates[i], 'value': np.exp(regression_line[i] + 2.5 * std_dev)} for i in range(len(all_dates))],
            "bot": [{'time': all_dates[i], 'value': np.exp(regression_line[i] - 2.0 * std_dev)} for i in range(len(all_dates))]
        }

        # Fiyat verisi
        price_data = []
        for i in range(len(dates)):
            price_data.append({'time': dates[i], 'value': prices[i]})

        return price_data, line_data, bands
    except Exception as e:
        print(f"Error: {e}")
        return None, None, None

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []

    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            # Maksimum veri
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=1000)
            if len(bars) < 100: continue

            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            prices = df['close'].tolist()
            dates = pd.to_datetime(df['time'], unit='ms').dt.strftime('%Y-%m-%d').tolist()

            price_data, line_data, bands = get_projections(prices, dates)

            if price_data:
                results.append({
                    'symbol': symbol,
                    'price': f"{prices[-1]:.6g}",
                    'price_data': price_data,
                    'line_data': line_data,
                    'bands': bands
                })
            time.sleep(0.05)
        except Exception as e:
            print(f"Error on {symbol}: {e}")
            continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    # Tüm veriyi JS'e aktarmak yerine sadece seçili coini yükleyeceğiz
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Crypto Regression Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js"></script>
        <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Poppins', sans-serif; background-color: #0f172a; color: white; }}
            .card {{ background: #1e293b; border-radius: 16px; transition: 0.3s; }}
            .card:hover {{ transform: translateY(-3px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }}
            #chart-container {{ width: 100%; height: 70vh; }}
        </style>
    </head>
    <body class="p-6">
        <header class="flex justify-between items-center pb-8 border-b border-slate-700 mb-8">
            <h1 class="text-3xl font-bold text-white">Log Regression <span class="text-sky-400">Dashboard</span></h1>
            <span class="text-sm text-slate-400 font-mono">{full_update} UTC</span>
        </header>

        <div class="grid grid-cols-3 md:grid-cols-6 lg:grid-cols-8 gap-3 mb-6">
    """

    for i in data:
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        html += f"""
        <button onclick="loadChart('{encoded_data}')" class="card p-3 text-center cursor-pointer hover:bg-slate-700">
            <div class="text-sm font-bold text-white font-mono">{i['symbol']}</div>
            <div class="text-xs text-sky-400 font-semibold">${i['price']}</div>
        </button>
        """

    html += f"""
        </div>
        
        <div class="card p-4">
            <h2 id="chart-title" class="text-xl font-bold mb-3 text-center">Coin Seçin</h2>
            <div id="chart-container"></div>
        </div>

        <script>
            let chart = null;
            let priceSeries = null;
            let lineSeries = null;
            let topBandSeries = null;
            let botBandSeries = null;

            function loadChart(encodedData) {{
                const data = JSON.parse(atob(encodedData));
                document.getElementById('chart-title').innerText = data.symbol + " Log Regression & Projection to 2050";
                
                if (chart) {{
                    chart.remove();
                }}

                chart = LightweightCharts.createChart(document.getElementById('chart-container'), {{
                    layout: {{ backgroundColor: '#1e293b', textColor: '#d1d5db' }},
                    grid: {{ vertLines: {{ color: '#334155' }}, horzLines: {{ color: '#334155' }} }},
                    rightPriceScale: {{ scaleMargins: {{ top: 0.1, bottom: 0.1 }}, mode: LightweightCharts.PriceScaleMode.Logarithmic }},
                    timeScale: {{ borderColor: '#334155', timeVisible: true, secondsVisible: false }},
                    crosshair: {{ mode: LightweightCharts.CrosshairMode.Normal }},
                }});

                priceSeries = chart.addLineSeries({{ color: '#38bdf8', lineWidth: 2, title: 'Price' }});
                lineSeries = chart.addLineSeries({{ color: '#eab308', lineWidth: 1, lineStyle: LightweightCharts.LineStyle.Dashed, title: 'Regression Line' }});
                topBandSeries = chart.addLineSeries({{ color: '#ef4444', lineWidth: 1, title: 'Upper Band' }});
                botBandSeries = chart.addLineSeries({{ color: '#22c55e', lineWidth: 1, title: 'Lower Band' }});

                priceSeries.setData(data.price_data);
                lineSeries.setData(data.line_data);
                topBandSeries.setData(data.bands.top);
                botBandSeries.setData(data.bands.bot);
            }}
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    create_html(analyze_market())
