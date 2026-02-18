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
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal = macd.ewm(span=9, adjust=False).mean()

    vol_change = df['volume'].pct_change()
    
    return {
        'rsi': rsi.iloc[-1],
        'macd': macd.iloc[-1],
        'signal': signal.iloc[-1],
        'vol_change': vol_change.iloc[-1],
        'close': df['close'].iloc[-1]
    }

def get_signal_data(tech_data):
    score = 0
    if tech_data['rsi'] < 30: score += 2
    elif tech_data['rsi'] > 70: score -= 2
    elif 30 < tech_data['rsi'] < 40: score += 1
    elif 60 < tech_data['rsi'] < 70: score -= 1

    if tech_data['macd'] > tech_data['signal']: score += 2
    else: score -= 2

    if tech_data['vol_change'] > 0.5: score += 1
    elif tech_data['vol_change'] < -0.5: score -= 1

    if score >= 3: return "STRONG BUY", "#166534" 
    elif score == 2: return "BUY", "#4ade80" 
    elif score <= -3: return "STRONG SELL", "#991b1b" 
    elif score == -2: return "SELL", "#f87171" 
    else: return "NEUTRAL", "#475569" 

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
            time.sleep(0.01) # Hızlandırıldı
        except: continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BasedVector | Professional Heatmap</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Montserrat', sans-serif; background-color: #0f172a; color: white; }}
            .gradient-text {{
                background: linear-gradient(to right, #991b1b, #f87171, #475569, #4ade80, #166534);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .disclaimer-bar {{
                background: rgba(30, 41, 59, 0.5);
                border-bottom: 1px solid #334155;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }}
            .coin-box {{ border-radius: 6px; transition: all 0.2s ease; border: 1px solid rgba(255,255,255,0.05); }}
            .coin-box:hover {{ transform: translateY(-2px); z-index: 10; box-shadow: 0 10px 20px rgba(0,0,0,0.4); border-color: rgba(255,255,255,0.2); }}
            .modal {{ display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.85); backdrop-filter: blur(8px); }}
            .modal-content {{ background-color: #1e293b; margin: 10% auto; padding: 30px; border-radius: 20px; width: 340px; border: 1px solid #334155; }}
            .star-btn {{ cursor: pointer; transition: 0.2s; font-size: 1.2rem; line-height: 1; }}
            input {{ transition: 0.3s; }}
            input:focus {{ box-shadow: 0 0 0 2px #38bdf8; }}
        </style>
    </head>
    <body>
        <div class="disclaimer-bar p-2 text-center text-slate-400">
            <strong>Legal Disclaimer:</strong> BasedVector is an analytical tool. The information provided does not constitute investment advice. Cryptocurrency trading carries high risk.
        </div>

        <div class="p-6">
            <header class="flex flex-col lg:flex-row justify-between items-center pb-8 border-b border-slate-800 mb-8 gap-6">
                <h1 class="text-4xl font-extrabold gradient-text tracking-tighter">BasedVector</h1>
                
                <div class="flex flex-wrap gap-4 items-center justify-center">
                    <div class="relative">
                        <input type="text" id="search-input" placeholder="Search Assets..." onkeyup="filterCoins()" class="bg-slate-900 border border-slate-700 text-white px-4 py-2 rounded-xl text-sm outline-none w-64">
                    </div>
                    <button onclick="toggleFavoritesFilter()" id="fav-filter-btn" class="bg-sky-600 hover:bg-sky-500 text-white px-5 py-2 rounded-xl text-sm font-bold transition-all shadow-lg shadow-sky-900/20">Show Favorites</button>
                    <div class="text-[10px] text-slate-500 font-mono bg-slate-900/50 px-3 py-1 rounded-full border border-slate-800">
                        LAST UPDATE: {full_update} UTC
                    </div>
                </div>
            </header>

            <div class="grid grid-cols-4 md:grid-cols-8 lg:grid-cols-10 xl:grid-cols-12 gap-2" id="coin-grid">
    """

    for i in data:
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        html += f"""
        <div class="coin-box p-4 text-center cursor-pointer relative" style="background-color: {i['color']}CC;" onclick="openModal('{encoded_data}')" data-symbol="{i['symbol']}">
            <span class="star-btn absolute top-1 left-1 text-slate-400 opacity-40 hover:opacity-100" onclick="toggleFav(event, '{i['symbol']}')">★</span>
            <span class="font-bold font-mono text-xs block mt-1">{i['symbol']}</span>
        </div>
        """

    html += """
            </div>
        </div>

        <div id="detailModal" class="modal" onclick="closeModalOutside(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="flex justify-between items-center mb-8 border-b border-slate-700 pb-4">
                    <h2 id="m-title" class="text-3xl font-black tracking-tight text-white"></h2>
                    <button onclick="closeModal()" class="text-slate-500 hover:text-white text-3xl transition">&times;</button>
                </div>
                <div id="m-body" class="space-y-5"></div>
                <button onclick="closeModal()" class="w-full mt-8 bg-slate-700 hover:bg-slate-600 py-3 rounded-xl font-bold transition">Close</button>
            </div>
        </div>

        <script>
            let favorites = JSON.parse(localStorage.getItem('favs')) || [];
            let showingFavsOnly = false;

            function openModal(encodedData) {
                const data = JSON.parse(atob(encodedData));
                document.getElementById('m-title').innerText = data.symbol;
                document.getElementById('m-body').innerHTML = `
                    <div class="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg">
                        <span class="text-slate-400 text-xs">PRICE</span>
                        <span class="font-mono font-bold text-lg text-white">$${data.price}</span>
                    </div>
                    <div class="flex justify-between items-center bg-slate-900/50 p-3 rounded-lg">
                        <span class="text-slate-400 text-xs">SIGNAL</span>
                        <span class="font-bold px-3 py-1 rounded-full text-xs" style="background:${data.color}; color:white">${data.signal_type}</span>
                    </div>
                    <div class="grid grid-cols-2 gap-3 mt-4">
                        <div class="bg-slate-900/50 p-3 rounded-lg text-center">
                            <div class="text-slate-500 text-[10px] mb-1">RSI</div>
                            <div class="font-bold text-white">${data.rsi}</div>
                        </div>
                        <div class="bg-slate-900/50 p-3 rounded-lg text-center">
                            <div class="text-slate-500 text-[10px] mb-1">MACD</div>
                            <div class="font-bold text-white">${data.macd}</div>
                        </div>
                    </div>
                `;
                document.getElementById('detailModal').style.display = 'block';
            }

            function closeModal() { document.getElementById('detailModal').style.display = 'none'; }
            function closeModalOutside(e) { if(e.target.id === 'detailModal') closeModal(); }

            function toggleFav(event, symbol) {
                event.stopPropagation();
                if (favorites.includes(symbol)) {
                    favorites = favorites.filter(f => f !== symbol);
                } else {
                    favorites.push(symbol);
                }
                localStorage.setItem('favs', JSON.stringify(favorites));
                updateStars();
                if (showingFavsOnly) filterCoins();
            }

            function updateStars() {
                document.querySelectorAll('.coin-box').forEach(box => {
                    const symbol = box.getAttribute('data-symbol');
                    const star = box.querySelector('.star-btn');
                    if (favorites.includes(symbol)) {
                        star.style.color = '#fbbf24';
                        star.style.opacity = '1';
                    } else {
                        star.style.color = '';
                        star.style.opacity = '';
                    }
                });
            }

            function filterCoins() {
                const term = document.getElementById('search-input').value.toUpperCase();
                document.querySelectorAll('.coin-box').forEach(box => {
                    const symbol = box.getAttribute('data-symbol');
                    const matchesSearch = symbol.includes(term);
                    const matchesFav = showingFavsOnly ? favorites.includes(symbol) : true;
                    box.style.display = (matchesSearch && matchesFav) ? 'block' : 'none';
                });
            }

            function toggleFavoritesFilter() {
                showingFavsOnly = !showingFavsOnly;
                document.getElementById('fav-filter-btn').innerText = showingFavsOnly ? 'Show All' : 'Show Favorites';
                document.getElementById('fav-filter-btn').classList.toggle('bg-sky-600');
                document.getElementById('fav-filter-btn').classList.toggle('bg-amber-500');
                filterCoins();
            }

            updateStars();
        </script>
    </body>
    </html>
    """
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    create_html(analyze_market())
