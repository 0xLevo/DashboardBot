import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json
import base64

# --- GENİŞLETİLMİŞ COIN LISTESİ (TOP 150 - Stabil hariç) ---
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX',
    'LINK', 'MATIC', 'TON', 'SHIB', 'LTC', 'BCH', 'ATOM', 'UNI', 'NEAR', 'INJ',
    'OP', 'ICP', 'FIL', 'LDO', 'TIA', 'STX', 'APT', 'ARB', 'RNDR', 'VET',
    'KAS', 'ETC', 'ALGO', 'RUNE', 'EGLD', 'SEI', 'SUI', 'AAVE', 'FTM', 'SAND',
    'IMX', 'MANA', 'GRT', 'FLOW', 'GALA', 'DYDX', 'QNT', 'MKR', 'WLD', 'APE',
    'SNX', 'AXS', 'CHZ', 'LUNC', 'PEPE', 'BONK', 'ORDI', 'FET', 'RBN', 'EOS',
    'MINA', 'XLM', 'XTZ', 'THETA', 'KAVA', 'KLAY', 'CAKE', 'ASTR', 'JUP', 'WIF',
    'PYTH', 'ORBS', 'ZIL', 'QTUM', 'GLMR', 'ANKR', 'ROSE', 'IOTX', 'DASH', 'ZEC'
]

def calculate_technical_indicators(df):
    """MACD, RSI ve Hacim değişimlerini hesaplar."""
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    # Hacim Değişimi
    vol_change = df['volume'].pct_change()
    
    return {
        'rsi': rsi.iloc[-1],
        'macd': macd.iloc[-1],
        'signal': signal.iloc[-1],
        'vol_change': vol_change.iloc[-1],
        'close': df['close'].iloc[-1]
    }

def get_signal_data(tech_data):
    """İndikatörleri harmanlayıp sinyal ve renk belirler."""
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

    # Renk Paleti (Belirgin -> Pastel)
    if score >= 3: return "STRONG BUY", "#166534" # Koyu Yeşil
    elif score == 2: return "BUY", "#4ade80" # Pastel Yeşil
    elif score <= -3: return "STRONG SELL", "#991b1b" # Koyu Kırmızı
    elif score == -2: return "SELL", "#f87171" # Pastel Kırmızı
    else: return "NEUTRAL", "#475569" # Gri

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []

    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=40)
            if len(bars) < 30: continue

            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            
            tech_data = calculate_technical_indicators(df)
            signal, color = get_signal_data(tech_data)

            results.append({
                'symbol': symbol,
                'price': f"{tech_data['close']:.6g}",
                'rsi': f"{tech_data['rsi']:.1f}",
                'macd': f"{tech_data['macd']:.2f}",
                'signal_type': signal,
                'color': color
            })
            time.sleep(0.05)
        except Exception as e:
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
            .modal {{ display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.7); }}
            .modal-content {{ background-color: #1e293b; margin: 15% auto; padding: 20px; border-radius: 12px; width: 300px; border: 1px solid #334155; }}
        </style>
    </head>
    <body class="p-6">
        <header class="flex justify-between items-center pb-8 border-b border-slate-700 mb-8">
            <h1 class="text-3xl font-bold font-mono">
                <span style="color: #991b1b">B</span><span style="color: #ef4444">a</span><span style="color: #475569">s</span><span style="color: #22c55e">e</span><span style="color: #166534">d</span>
                <span style="color: #991b1b">V</span><span style="color: #ef4444">e</span><span style="color: #475569">c</span><span style="color: #22c55e">t</span><span style="color: #166535">o</span><span style="color: #166535">r</span>
                <span class="text-white">Heatmap</span>
            </h1>
            <div class="flex gap-2">
                <button onclick="toggleFavorites()" id="fav-btn" class="bg-slate-700 text-white px-4 py-2 rounded-lg text-sm font-semibold">Show Favorites</button>
                <span class="text-sm text-slate-400 font-mono self-center">{full_update} UTC</span>
            </div>
        </header>

        <div class="grid grid-cols-5 md:grid-cols-8 lg:grid-cols-12 gap-2" id="coin-grid">
    """

    for i in data:
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        html += f"""
        <div class="coin-box relative p-2 text-center cursor-pointer" style="background-color: {i['color']};" onclick="openModal('{encoded_data}')">
            <span id="star-{i['symbol']}" class="absolute top-0 left-1 text-xs text-slate-300">★</span>
            <span class="font-bold font-mono text-xs">{i['symbol']}</span>
        </div>
        """

    html += """
        </div>

        <div id="detailModal" class="modal">
            <div class="modal-content">
                <div class="flex justify-between mb-4">
                    <h2 id="m-title" class="text-2xl font-bold"></h2>
                    <button onclick="closeModal()" class="text-slate-400 hover:text-white">&times;</button>
                </div>
                <div id="m-body" class="text-sm text-slate-300 space-y-2"></div>
            </div>
        </div>

        <footer class="mt-12 pt-6 border-t border-slate-700 text-center text-slate-500 text-xs">
            <p><strong>LEGAL DISCLAIMER:</strong> The information provided on BasedVector is for informational purposes only and does not constitute financial advice. Trading cryptocurrencies involves significant risk.</p>
        </footer>

        <script>
            let favorites = JSON.parse(localStorage.getItem('favs')) || [];
            let showingFavs = false;

            function openModal(encodedData) {
                const data = JSON.parse(atob(encodedData));
                document.getElementById('m-title').innerText = data.symbol;
                document.getElementById('m-body').innerHTML = `
                    <p>Price: <strong>$${data.price}</strong></p>
                    <p>Signal: <strong>${data.signal_type}</strong></p>
                    <p>RSI: <strong>${data.rsi}</strong></p>
                    <p>MACD: <strong>${data.macd}</strong></p>
                `;
                document.getElementById('detailModal').style.display = 'block';
                
                // Yıldız Tıklama Kontrolü (Modal açıkken yıldız tıklanırsa)
                event.stopPropagation(); 
            }

            function closeModal() {
                document.getElementById('detailModal').style.display = 'none';
            }

            function toggleFav(symbol) {
                if (favorites.includes(symbol)) {
                    favorites = favorites.filter(f => f !== symbol);
                } else {
                    favorites.push(symbol);
                }
                localStorage.setItem('favs', JSON.stringify(favorites));
                updateStars();
                if (showingFavs) renderGrid();
                event.stopPropagation(); // Kutu tıklamasını engelle
            }

            function updateStars() {
                document.querySelectorAll('.coin-box').forEach(box => {
                    const symbol = box.querySelector('.font-mono').innerText;
                    const star = box.querySelector('span.absolute');
                    if (favorites.includes(symbol)) {
                        star.style.color = '#facc15'; // Sarı yıldız
                        star.style.opacity = '1';
                    } else {
                        star.style.color = '#cbd5e1'; // Soluk yıldız
                        star.style.opacity = '0.5';
                    }
                });
            }

            function toggleFavorites() {
                showingFavs = !showingFavs;
                document.getElementById('fav-btn').innerText = showingFavs ? 'Show All' : 'Show Favorites';
                renderGrid();
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
            
            // Modal dışına tıklayınca kapat
            window.onclick = function(event) {
                const modal = document.getElementById('detailModal');
                if (event.target == modal) {
                    modal.style.display = "none";
                }
            }
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    create_html(analyze_market())
