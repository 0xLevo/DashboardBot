import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json
import base64

# --- COIN LISTESI ---
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

def format_crypto_price(price):
    if price == 0: return "0.00"
    if price >= 1: return f"{price:.2f}"
    s = f"{price:.12f}"
    parts = s.split('.')
    decimal_part = parts[1]
    first_nonzero_idx = next((i for i, c in enumerate(decimal_part) if c != '0'), -1)
    if first_nonzero_idx == -1: return "0.00"
    return f"0.{decimal_part[:first_nonzero_idx + 3]}"

def calculate_metrics(df):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))

    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9, adjust=False).mean()

    vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
    current_price = df['close'].iloc[-1]
    cost_diff_pct = ((current_price - vwap) / vwap) * 100
    change_24h = ((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100

    return {
        'rsi': rsi.iloc[-1], 'macd': macd.iloc[-1], 'signal': signal_line.iloc[-1],
        'close': current_price, 'vwap': vwap, 'diff': cost_diff_pct, 'change': change_24h
    }

def get_enhanced_signal(data):
    score = 0
    if data['rsi'] < 30: score += 2
    elif data['rsi'] > 70: score -= 2
    if data['macd'] > data['signal']: score += 1
    else: score -= 1
    if data['diff'] < -30: score += 2
    elif data['diff'] > 50: score -= 2

    if score >= 3: return "STRONG BUY", "#1b4332"
    elif score >= 1: return "BUY", "#52b788" 
    elif score <= -3: return "STRONG SELL", "#7f1d1d" 
    elif score <= -1: return "SELL", "#e5989b" 
    else: return "NEUTRAL", "#475569" 

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []
    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=450)
            if len(bars) < 300: continue
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            data = calculate_metrics(df)
            signal_name, color = get_enhanced_signal(data)
            results.append({
                'symbol': symbol, 'price': format_crypto_price(data['close']),
                'change': f"{data['change']:+.2f}%", 'rsi': f"{data['rsi']:.1f}",
                'macd': f"{data['macd']:.4f}", 'vwap': format_crypto_price(data['vwap']),
                'diff': f"{data['diff']:.2f}", 'signal_type': signal_name, 'color': color
            })
            time.sleep(0.02)
        except: continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BasedVector | Smart Terminal</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Montserrat', sans-serif; background-color: #020617; color: white; }}
            .gradient-text {{ background: linear-gradient(to right, #991b1b, #52b788, #38bdf8); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .coin-box {{ border-radius: 4px; transition: 0.2s; border: 1px solid rgba(255,255,255,0.1); cursor: pointer; }}
            .coin-box:hover {{ transform: scale(1.05); z-index: 10; border-color: white; }}
            .modal {{ display: none; position: fixed; z-index: 100; inset: 0; background: rgba(0,0,0,0.9); backdrop-filter: blur(10px); }}
            .modal-content {{ background: #0f172a; margin: 5% auto; padding: 25px; border-radius: 20px; width: 90%; max-width: 400px; border: 1px solid #334155; }}
            .lang-btn {{ background: #1e293b; color: #94a3b8; padding: 5px 12px; border-radius: 6px; font-size: 11px; font-weight: 700; }}
            .lang-btn.active {{ background: #3b82f6; color: white; }}
            .star-btn {{ cursor: pointer; opacity: 0.3; transition: 0.2s; }}
            .star-btn.active {{ opacity: 1; color: #fbbf24; }}
        </style>
    </head>
    <body>
        <div id="disclaimer" class="p-2 text-center text-slate-500 font-bold text-[10px] uppercase tracking-widest bg-slate-950 border-b border-slate-900">
            Legal Disclaimer: BasedVector provides analytical data only. Not financial advice.
        </div>

        <div class="p-4 md:p-8">
            <header class="flex flex-col lg:flex-row justify-between items-center mb-8 gap-6 border-b border-slate-800 pb-8">
                <div class="flex flex-col items-start gap-3">
                    <a href="index.html"><h1 class="text-5xl font-black gradient-text tracking-tighter">BASEDVECTOR</h1></a>
                    <div class="flex gap-2">
                        <button onclick="changeLang('en')" id="btn-en" class="lang-btn active">EN</button>
                        <button onclick="changeLang('tr')" id="btn-tr" class="lang-btn">TR</button>
                        <button onclick="changeLang('zh')" id="btn-zh" class="lang-btn">ZH</button>
                    </div>
                </div>
                <div class="flex flex-wrap gap-3 items-center">
                    <input type="text" id="search-input" placeholder="Search..." onkeyup="filterCoins()" class="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg text-sm outline-none w-48 focus:border-blue-500">
                    <button onclick="toggleFavoritesFilter()" id="fav-filter-btn" class="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg text-sm font-bold transition">Show Favorites</button>
                    <div class="text-[10px] text-slate-500 font-mono bg-slate-950 px-3 py-2 rounded-full border border-slate-800 uppercase">SYNCED: {full_update}</div>
                </div>
            </header>

            <div class="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-10 lg:grid-cols-12 gap-2" id="coin-grid">
    """

    for i in data:
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        html += f"""
        <div class="coin-box p-3 text-center relative" style="background-color: {i['color']};" onclick="openModal('{encoded_data}')" data-symbol="{i['symbol']}">
            <div class="flex justify-start"><span class="star-btn" onclick="toggleFav(event, '{i['symbol']}')">★</span></div>
            <div class="font-bold text-[11px] font-mono mt-1">{i['symbol']}</div>
            <div class="text-[8px] opacity-80 font-bold">{i['change']}</div>
        </div>
        """

    html += """
            </div>
        </div>

        <div id="detailModal" class="modal" onclick="closeModalOutside(event)">
            <div class="modal-content" onclick="event.stopPropagation()">
                <div class="flex justify-between items-center mb-6">
                    <h2 id="m-title" class="text-4xl font-black"></h2>
                    <button onclick="closeModal()" class="text-3xl">&times;</button>
                </div>
                <div id="m-body" class="space-y-4"></div>
                <button id="close-btn" onclick="closeModal()" class="w-full mt-6 bg-slate-800 py-3 rounded-xl font-bold">Close</button>
            </div>
        </div>

        <script>
            const translations = {
                en: { search: "Search...", favs: "Show Favorites", all: "Show All", price: "Market Price", vwap: "Yearly Avg (VWAP)", diff: "Cost Distance", rsi: "RSI", macd: "MACD", close: "Close", signal: "SIGNAL" },
                tr: { search: "Varlık Ara...", favs: "Favoriler", all: "Hepsini Göster", price: "Piyasa Fiyatı", vwap: "Yıllık Ort. (VWAP)", diff: "Maliyet Uzaklığı", rsi: "RSI", macd: "MACD", close: "Kapat", signal: "SİNYAL" },
                zh: { search: "搜索...", favs: "显示收藏", all: "显示全部", price: "市场价格", vwap: "年度平均 (VWAP)", diff: "成本距离", rsi: "RSI", macd: "MACD", close: "关闭", signal: "信号" }
            };

            let currentLang = 'en';
            let favorites = JSON.parse(localStorage.getItem('favs')) || [];
            let favFilter = false;

            function changeLang(lang) {
                currentLang = lang;
                document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
                document.getElementById('btn-'+lang).classList.add('active');
                document.getElementById('search-input').placeholder = translations[lang].search;
                document.getElementById('fav-filter-btn').innerText = favFilter ? translations[lang].all : translations[lang].favs;
                document.getElementById('close-btn').innerText = translations[lang].close;
            }

            function openModal(enc) {
                const d = JSON.parse(atob(enc));
                const t = translations[currentLang];
                document.getElementById('m-title').innerText = d.symbol;
                document.getElementById('m-body').innerHTML = `
                    <div class="bg-black/40 p-4 rounded-xl">
                        <div class="text-[10px] text-slate-500 uppercase font-bold">${t.price}</div>
                        <div class="text-2xl font-mono">$${d.price} <span class="text-xs ${d.change.includes('+') ? 'text-green-400':'text-red-400'}">${d.change}</span></div>
                    </div>
                    <div class="grid grid-cols-2 gap-2">
                        <div class="bg-black/40 p-3 rounded-xl text-center">
                            <div class="text-[9px] text-slate-500 uppercase">${t.rsi}</div>
                            <div class="font-bold">${d.rsi}</div>
                        </div>
                        <div class="bg-black/40 p-3 rounded-xl text-center">
                            <div class="text-[9px] text-slate-500 uppercase">${t.macd}</div>
                            <div class="font-bold text-[10px]">${d.macd}</div>
                        </div>
                    </div>
                    <div class="bg-black/40 p-4 rounded-xl">
                        <div class="text-[10px] text-slate-500 uppercase font-bold">${t.vwap}</div>
                        <div class="text-xl font-mono text-blue-400">$${d.vwap}</div>
                        <div class="text-[10px] mt-1 font-bold">${t.diff}: <span class="${parseFloat(d.diff) < 0 ? 'text-red-400':'text-green-400'}">${d.diff}%</span></div>
                    </div>
                    <div class="py-3 text-center rounded-lg font-black tracking-widest text-sm" style="background-color:${d.color}">${t.signal}: ${d.signal_type}</div>
                `;
                document.getElementById('detailModal').style.display = 'block';
            }

            function closeModal() { document.getElementById('detailModal').style.display = 'none'; }
            function closeModalOutside(e) { if(e.target.id === 'detailModal') closeModal(); }
            function toggleFav(e, s) {
                e.stopPropagation();
                favorites = favorites.includes(s) ? favorites.filter(f => f !== s) : [...favorites, s];
                localStorage.setItem('favs', JSON.stringify(favorites));
                updateStars();
                if(favFilter) filterCoins();
            }
            function updateStars() {
                document.querySelectorAll('.coin-box').forEach(box => {
                    const s = box.getAttribute('data-symbol');
                    box.querySelector('.star-btn').className = favorites.includes(s) ? 'star-btn active' : 'star-btn';
                });
            }
            function filterCoins() {
                const term = document.getElementById('search-input').value.toUpperCase();
                document.querySelectorAll('.coin-box').forEach(box => {
                    const s = box.getAttribute('data-symbol');
                    const match = s.includes(term) && (!favFilter || favorites.includes(s));
                    box.style.display = match ? 'block' : 'none';
                });
            }
            function toggleFavoritesFilter() {
                favFilter = !favFilter;
                changeLang(currentLang);
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
