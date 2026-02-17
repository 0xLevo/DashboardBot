import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json
import base64

# --- COIN LISTESİ ---
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX',
    'LINK', 'MATIC', 'TON', 'SHIB', 'LTC', 'BCH', 'ATOM', 'UNI', 'NEAR', 'INJ',
    'OP', 'ICP', 'FIL', 'LDO', 'TIA', 'STX', 'APT', 'ARB', 'RNDR', 'VET',
    'KAS', 'ETC', 'ALGO', 'RUNE', 'EGLD', 'SEI', 'SUI', 'AAVE', 'FTM', 'SAND'
]

def calculate_technical_indicators(df):
    """MACD, RSI ve Hacim değişimlerini hesaplar."""
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['rsi'] = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['signal'] = df['macd'].ewm(span=9, adjust=False).mean()

    # Hacim Değişimi
    df['vol_change'] = df['volume'].pct_change()
    
    return df.iloc[-1]

def get_signal_color(tech_data):
    """İndikatörleri harmanlayıp sinyal rengini belirler."""
    score = 0
    
    # RSI Sinyalleri
    if tech_data['rsi'] < 30: score += 2  # Oversold (Buy)
    elif tech_data['rsi'] > 70: score -= 2 # Overbought (Sell)
    elif 30 < tech_data['rsi'] < 40: score += 1
    elif 60 < tech_data['rsi'] < 70: score -= 1

    # MACD Sinyalleri
    if tech_data['macd'] > tech_data['signal']: score += 2 # Bullish
    else: score -= 2 # Bearish

    # Hacim Sinyalleri
    if tech_data['vol_change'] > 0.5: score += 1 # High volume buy
    elif tech_data['vol_change'] < -0.5: score -= 1 # High volume sell

    # Renk ve Durum belirleme (Sadece renkler için)
    if score >= 3: return "#166534" # Strong Buy - Dark Green
    elif score == 2: return "#22c55e" # Buy - Light Green
    elif score <= -3: return "#991b1b" # Strong Sell - Dark Red
    elif score == -2: return "#ef4444" # Sell - Light Red
    else: return "#475569" # Neutral - Grey

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []

    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=30)
            if len(bars) < 20: continue

            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            
            tech_data = calculate_technical_indicators(df)
            color = get_signal_color(tech_data)

            results.append({
                'symbol': symbol,
                'price': f"{df['close'].iloc[-1]:.6g}",
                'rsi': f"{tech_data['rsi']:.1f}",
                'color': color
            })
            time.sleep(0.05)
        except Exception as e:
            print(f"Error on {symbol}: {e}")
            continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BasedVector Heatmap</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Montserrat', sans-serif; background-color: #0f172a; color: white; }}
            .coin-box {{ border-radius: 8px; transition: 0.2s; border: 1px solid rgba(255,255,255,0.1); }}
            .coin-box:hover {{ transform: scale(1.05); z-index: 10; box-shadow: 0 4px 15px rgba(0,0,0,0.5); }}
            .tooltip {{ visibility: hidden; background-color: black; color: white; text-align: center; border-radius: 6px; padding: 5px; position: absolute; z-index: 1; bottom: 125%; left: 50%; transform: translateX(-50%); opacity: 0; transition: opacity 0.3s; font-size: 0.75rem; }}
            .coin-box:hover .tooltip {{ visibility: visible; opacity: 1; }}
        </style>
    </head>
    <body class="p-6">
        <header class="flex justify-between items-center pb-8 border-b border-slate-700 mb-8">
            <h1 class="text-3xl font-bold">
                <span style="color: #38bdf8">Based</span><span style="color: #ef4444">Vector</span> <span class="text-white">Heatmap</span>
            </h1>
            <div class="flex gap-2">
                <button onclick="toggleFavorites()" id="fav-btn" class="bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-semibold">Show Favorites</button>
                <span class="text-sm text-slate-400 font-mono self-center">{full_update} UTC</span>
            </div>
        </header>

        <div class="grid grid-cols-5 md:grid-cols-8 lg:grid-cols-10 gap-2" id="coin-grid">
    """

    for i in data:
        html += f"""
        <div class="coin-box relative p-2 text-center cursor-pointer" style="background-color: {i['color']};" onclick="toggleFav('{i['symbol']}')">
            <span class="font-bold font-mono text-sm">{i['symbol']}</span>
            <div class="tooltip">
                ${i['price']}<br>RSI: {i['rsi']}
            </div>
            <span id="star-{i['symbol']}" class="absolute top-0 right-1 text-xs opacity-0 hover:opacity-100">★</span>
        </div>
        """

    html += """
        </div>

        <footer class="mt-12 pt-6 border-t border-slate-700 text-center text-slate-500 text-xs">
            <p><strong>LEGAL DISCLAIMER:</strong> The information provided on BasedVector is for informational purposes only and does not constitute financial advice. Trading cryptocurrencies involves significant risk.</p>
        </footer>

        <script>
            let favorites = JSON.parse(localStorage.getItem('favs')) || [];
            let showingFavs = false;

            function toggleFav(symbol) {
                if (favorites.includes(symbol)) {
                    favorites = favorites.filter(f => f !== symbol);
                } else {
                    favorites.push(symbol);
                }
                localStorage.setItem('favs', JSON.stringify(favorites));
                updateStars();
                if (showingFavs) renderGrid();
            }

            function toggleFavorites() {
                showingFavs = !showingFavs;
                document.getElementById('fav-btn').innerText = showingFavs ? 'Show All' : 'Show Favorites';
                renderGrid();
            }

            function updateStars() {
                document.querySelectorAll('.coin-box').forEach(box => {
                    const symbol = box.querySelector('.font-mono').innerText;
                    const star = box.querySelector('span.absolute');
                    if (favorites.includes(symbol)) {
                        star.classList.remove('opacity-0');
                        star.style.color = 'yellow';
                    } else {
                        star.classList.add('opacity-0');
                    }
                });
            }

            function renderGrid() {
                const grid = document.getElementById('coin-grid');
                const boxes = grid.getElementsByClassName('coin-box');
                for (let box of boxes) {
                    const symbol = box.querySelector('.font-mono').innerText;
                    if (showingFavs && !favorites.includes(symbol)) {
                        box.style.display = 'none';
                    } else {
                        box.style.display = 'block';
                    }
                }
            }

            // Sayfa yüklendiğinde favori yıldızlarını göster
            updateStars();
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    create_html(analyze_market())
