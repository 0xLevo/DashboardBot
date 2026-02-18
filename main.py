import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json
import base64

# --- TOP 200 COINS (Stabil hariç) ---
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX',
    'LINK', 'MATIC', 'TON', 'SHIB', 'LTC', 'BCH', 'NEAR', 'UNI', 'LEO', 'PEPE',
    'ICP', 'APT', 'RNDR', 'HBAR', 'FIL', 'XLM', 'ARB', 'ATOM', 'STX', 'OKB',
    'IMX', 'KAS', 'VET', 'LDO', 'MKR', 'TIA', 'GRT', 'THETA', 'FTM', 'SEI',
    'SUI', 'OP', 'INJ', 'RUNE', 'FLOKI', 'LUNC', 'BEAM', 'GALA', 'PENDLE', 'DYDX',
    'AAVE', 'ORDI', 'WIF', 'BONK', 'PYTH', 'JUP', 'FET', 'AGIX', 'OCEAN', 'RBN',
    'EGLD', 'FLOW', 'MINA', 'QNT', 'AXS', 'CHZ', 'MANA', 'SAND', 'EOS', 'XTZ',
    'IOTA', 'KAVA', 'KLAY', 'CAKE', 'ASTR', 'ZIL', 'QTUM', 'GLMR', 'ANKR', 'ROSE',
    'IOTX', 'DASH', 'ZEC', 'XMR', 'WLD', 'STRK', 'DYM', 'MANTA', 'ALT', 'RON',
    'PIXEL', 'CKB', 'BTT', 'HOT', 'GMT', 'GNS', 'GMX', 'SNX', 'CRV', 'ENS',
    'LRC', 'MASK', 'WOO', 'CVX', 'BAL', 'SUSHI', 'YFI', '1INCH', 'ZRX', 'UMA',
    'BAND', 'NMR', 'GLM', 'JASMY', 'CELO', 'TWT', 'ID', 'EDU', 'HOOK', 'ARKM',
    'MAV', 'CYBER', 'NTRN', 'SATS', 'RATS', 'MYRO', 'MUBI', 'TURBO', 'MEME', 'POPCAT',
    'BRETT', 'MOG', 'MEW', 'BOME', 'SLERF', 'DEGEN', 'AEVO', 'METIS', 'SCRT', 'ONT',
    'SKL', 'CVC', 'SC', 'BLZ', 'RAY', 'SRM', 'STG', 'RDNT', 'MAGIC', 'GAL'
]

def calculate_metrics(df):
    # RSI Hesaplama
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))

    # MACD Hesaplama
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9, adjust=False).mean()

    # Hacim Değişimi
    vol_change = df['volume'].pct_change().rolling(5).mean()

    # TARİHSEL VWAP (Ağırlıklı Ortalama Maliyet - Son 100 Gün)
    vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
    current_price = df['close'].iloc[-1]
    cost_diff_pct = ((current_price - vwap) / vwap) * 100

    return {
        'rsi': rsi.iloc[-1],
        'macd': macd.iloc[-1],
        'signal': signal_line.iloc[-1],
        'vol_change': vol_change.iloc[-1],
        'close': current_price,
        'vwap': vwap,
        'diff': cost_diff_pct
    }

def get_signal_data(tech_data):
    score = 0
    if tech_data['rsi'] < 30: score += 2
    elif tech_data['rsi'] > 70: score -= 2
    if tech_data['macd'] > tech_data['signal']: score += 2
    else: score -= 2
    
    # Renk Paleti (Pastel & Göz Yormayan)
    if score >= 3: return "STRONG BUY", "#1b4332"
    elif score >= 1: return "BUY", "#52b788" 
    elif score <= -3: return "STRONG SELL", "#7f1d1d" 
    elif score <= -1: return "SELL", "#e5989b" 
    else: return "NEUTRAL", "#475569" 

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []
    print("Market verileri analiz ediliyor...")
    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            # Maliyet analizi için daha fazla veri (100 gün) çekiyoruz
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=100)
            if len(bars) < 50: continue
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            
            data = calculate_metrics(df)
            signal_name, color = get_signal_data(data)
            
            results.append({
                'symbol': symbol,
                'price': f"{data['close']:.6g}",
                'rsi': f"{data['rsi']:.1f}",
                'macd': f"{data['macd']:.4f}",
                'vwap': f"{data['vwap']:.6g}",
                'diff': f"{data['diff']:.2f}",
                'signal_type': signal_name,
                'color': color
            })
            time.sleep(0.01)
        except: continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <!DOCTYPE html><html lang="tr">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BasedVector | Maliyet Analizi</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Montserrat', sans-serif; background-color: #020617; color: white; }}
            .gradient-text {{
                background: linear-gradient(to right, #991b1b, #f87171, #475569, #52b788, #1b4332);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            .coin-box {{ 
                border-radius: 4px; 
                transition: all 0.2s ease; 
                border: 2px solid rgba(255, 255, 255, 0.2); 
            }}
            .coin-box:hover {{ transform: scale(1.08); z-index: 50; border-color: rgba(255, 255, 255, 0.6); }}
            .modal {{ display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); backdrop-filter: blur(12px); }}
            .modal-content {{ background: #0f172a; margin: 5% auto; padding: 32px; border-radius: 24px; width: 400px; border: 1px solid #334155; }}
            .star-btn {{ cursor: pointer; transition: 0.2s; font-size: 1.1rem; }}
        </style>
    </head>
    <body>
        <div class="p-2 text-center text-slate-500 font-bold text-[10px] uppercase tracking-widest bg-slate-950 border-b border-slate-900">
            BasedVector Analitik Veri Paneli | Finansal Tavsiye Değildir
        </div>

        <div class="p-4 md:p-8">
            <header class="flex flex-col lg:flex-row justify-between items-center pb-8 border-b border-slate-800 mb-8 gap-6">
                <a href="index.html" class="no-underline hover:opacity-80 transition">
                    <h1 class="text-5xl font-black gradient-text tracking-tight cursor-pointer">BasedVector</h1>
                </a>
                <div class="flex flex-wrap gap-4 items-center justify-center">
                    <input type="text" id="search-input" placeholder="Varlık Ara..." onkeyup="filterCoins()" class="bg-slate-900 border border-slate-700 text-white px-5 py-2 rounded-xl text-sm outline-none w-72 focus:border-sky-500">
                    <button onclick="toggleFavoritesFilter()" id="fav-filter-btn" class="bg-sky-600 hover:bg-sky-500 text-white px-6 py-2 rounded-xl text-sm font-bold transition-all">Favorileri Göster</button>
                    <div class="text-[10px] text-slate-500 font-mono bg-slate-950 px-4 py-2 rounded-full border border-slate-800 uppercase">GÜNCEL: {full_update}</div>
                </div>
            </header>

            <div class="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-10 lg:grid-cols-12 xl:grid-cols-14 gap-2" id="coin-grid">
    """

    for i in data:
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        html += f"""
        <div class="coin-box p-3 text-center cursor-pointer relative" style="background-color: {i['color']};" onclick="openModal('{encoded_data}')" data-symbol="{i['symbol']}">
            <div class="flex justify-start"><span class="star-btn text-white opacity-40" onclick="toggleFav(event, '{i['symbol']}')">★</span></div>
            <span class="font-bold font-mono text-[11px] block mt-1">{i['symbol']}</span>
        </div>
        """

    html += """
            </div>
        </div>

        <div id="detailModal" class="modal" onclick="closeModalOutside(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="flex justify-between items-center mb-6">
                    <h2 id="m-title" class="text-4xl font-black text-white"></h2>
                    <button onclick="closeModal()" class="text-slate-500 hover:text-white text-4xl">&times;</button>
                </div>
                <div id="m-body" class="space-y-3"></div>
                <button onclick="closeModal()" class="w-full mt-6 bg-slate-800 hover:bg-slate-700 py-4 rounded-2xl font-bold transition">Kapat</button>
            </div>
        </div>

        <script>
            let favorites = JSON.parse(localStorage.getItem('favs')) || [];
            let showingFavsOnly = false;

            function openModal(encodedData) {
                const data = JSON.parse(atob(encodedData));
                const diffColor = parseFloat(data.diff) >= 0 ? '#4ade80' : '#f87171';
                
                document.getElementById('m-title').innerText = data.symbol;
                document.getElementById('m-body').innerHTML = `
                    <div class="p-4 bg-slate-950 rounded-xl border border-slate-800">
                        <div class="text-slate-500 text-[10px] mb-1 uppercase font-bold tracking-wider">Güncel Piyasa Fiyatı</div>
                        <div class="font-mono text-2xl font-bold text-white">$${data.price}</div>
                    </div>
                    
                    <div class="grid grid-cols-1 gap-3">
                        <div class="p-4 bg-slate-950 rounded-xl border border-slate-800">
                            <div class="text-slate-500 text-[10px] mb-1 uppercase font-bold tracking-wider">Ortalama Satın Alma Maliyeti (VWAP 100G)</div>
                            <div class="font-mono text-xl font-bold text-sky-400">$${data.vwap}</div>
                        </div>
                        <div class="p-4 bg-slate-950 rounded-xl border border-slate-800">
                            <div class="text-slate-500 text-[10px] mb-1 uppercase font-bold tracking-wider">Ortalamadan Uzaklık (Maliyet Farkı)</div>
                            <div class="font-mono text-xl font-bold" style="color:${diffColor}">${data.diff}%</div>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3 pt-2">
                        <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                            <div class="text-slate-500 text-[10px] mb-1">RSI (14)</div>
                            <div class="font-bold text-lg">${data.rsi}</div>
                        </div>
                        <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                            <div class="text-slate-500 text-[10px] mb-1">MACD</div>
                            <div class="font-bold text-lg">${data.macd}</div>
                        </div>
                    </div>
                    <div class="mt-4 text-center py-2 rounded-lg font-black tracking-widest text-sm" style="background-color:${data.color}">
                        SİNYAL: ${data.signal_type}
                    </div>
                `;
                document.getElementById('detailModal').style.display = 'block';
            }

            function closeModal() { document.getElementById('detailModal').style.display = 'none'; }
            function closeModalOutside(e) { if(e.target.id === 'detailModal') closeModal(); }
            function toggleFav(event, symbol) {
                event.stopPropagation();
                if (favorites.includes(symbol)) { favorites = favorites.filter(f => f !== symbol); } 
                else { favorites.push(symbol); }
                localStorage.setItem('favs', JSON.stringify(favorites));
                updateStars();
                if (showingFavsOnly) filterCoins();
            }
            function updateStars() {
                document.querySelectorAll('.coin-box').forEach(box => {
                    const symbol = box.getAttribute('data-symbol');
                    const star = box.querySelector('.star-btn');
                    if (favorites.includes(symbol)) { star.style.color = '#fbbf24'; star.style.opacity = '1'; } 
                    else { star.style.color = ''; star.style.opacity = ''; }
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
                document.getElementById('fav-filter-btn').innerText = showingFavsOnly ? 'Tüm Varlıkları Göster' : 'Favorileri Göster';
                document.getElementById('fav-filter-btn').classList.toggle('bg-sky-600');
                document.getElementById('fav-filter-btn').classList.toggle('bg-amber-600');
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
