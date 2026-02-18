import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json
import base64

# --- TOP 200 COINS (Excluding Stables) ---
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
    # RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))

    # MACD
    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9, adjust=False).mean()

    # TARİHSEL VWAP (Ağırlıklı Ortalama Maliyet - SON 365 GÜN)
    # 300 gün ve üzeri veri kullanarak piyasanın uzun vadeli maliyet tabanını hesaplar
    vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
    current_price = df['close'].iloc[-1]
    cost_diff_pct = ((current_price - vwap) / vwap) * 100

    return {
        'rsi': rsi.iloc[-1],
        'macd': macd.iloc[-1],
        'signal': signal_line.iloc[-1],
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
    
    if score >= 3: return "STRONG BUY", "#1b4332"
    elif score >= 1: return "BUY", "#52b788" 
    elif score <= -3: return "STRONG SELL", "#7f1d1d" 
    elif score <= -1: return "SELL", "#e5989b" 
    else: return "NEUTRAL", "#475569" 

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []
    print("Analyzing Market Data (365D Lookback)... Please wait.")
    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            # 300+ gün analiz için limiti 450 yapıyoruz
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=450)
            if len(bars) < 300: continue # Yeterli geçmişi olmayan coinleri eliyoruz
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
            time.sleep(0.02) # Rate limit koruması
        except: continue
    return results

def create_html(data):
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BasedVector | 365D Cost Analysis</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Montserrat', sans-serif; background-color: #020617; color: white; }}
            .gradient-text {{ background: linear-gradient(to right, #991b1b, #f87171, #475569, #52b788, #1b4332); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
            .coin-box {{ border-radius: 4px; transition: all 0.2s ease; border: 2px solid rgba(255, 255, 255, 0.2); }}
            .coin-box:hover {{ transform: scale(1.08); z-index: 50; border-color: rgba(255, 255, 255, 0.6); }}
            .modal {{ display: none; position: fixed; z-index: 100; left: 0; top: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.9); backdrop-filter: blur(12px); }}
            .modal-content {{ background: #0f172a; margin: 5% auto; padding: 32px; border-radius: 24px; width: 400px; border: 1px solid #334155; }}
            .lang-btn {{ background: #1e293b; color: #94a3b8; padding: 4px 10px; border-radius: 8px; font-size: 11px; font-weight: 700; transition: 0.3s; }}
            .lang-btn.active {{ background: #38bdf8; color: white; }}
            .star-btn {{ cursor: pointer; transition: 0.2s; font-size: 1.1rem; }}
        </style>
    </head>
    <body>
        <div id="disclaimer" class="p-2 text-center text-slate-500 font-bold text-[10px] uppercase tracking-widest bg-slate-950 border-b border-slate-900">
            Legal Disclaimer: BasedVector provides analytical data only. Not financial advice. Trading involves high risk.
        </div>

        <div class="p-4 md:p-8">
            <header class="flex flex-col lg:flex-row justify-between items-center pb-8 border-b border-slate-800 mb-8 gap-6">
                <div class="flex flex-col items-start gap-2">
                    <a href="index.html" class="no-underline hover:opacity-80 transition">
                        <h1 class="text-5xl font-black gradient-text tracking-tight cursor-pointer">BasedVector</h1>
                    </a>
                    <div class="flex gap-2">
                        <button onclick="changeLang('en')" id="btn-en" class="lang-btn active">EN</button>
                        <button onclick="changeLang('tr')" id="btn-tr" class="lang-btn">TR</button>
                        <button onclick="changeLang('zh')" id="btn-zh" class="lang-btn">ZH</button>
                    </div>
                </div>

                <div class="flex flex-wrap gap-4 items-center justify-center">
                    <input type="text" id="search-input" placeholder="Search Assets..." onkeyup="filterCoins()" class="bg-slate-900 border border-slate-700 text-white px-5 py-2 rounded-xl text-sm outline-none w-64 focus:border-sky-500">
                    <button onclick="toggleFavoritesFilter()" id="fav-filter-btn" class="bg-sky-600 hover:bg-sky-500 text-white px-6 py-2 rounded-xl text-sm font-bold transition-all">Show Favorites</button>
                    <div class="text-[10px] text-slate-500 font-mono bg-slate-950 px-4 py-2 rounded-full border border-slate-800 uppercase">SYNCED: {full_update}</div>
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
                <button id="close-modal-btn" onclick="closeModal()" class="w-full mt-6 bg-slate-800 hover:bg-slate-700 py-4 rounded-2xl font-bold transition">Close</button>
            </div>
        </div>

        <script>
            const translations = {
                en: {
                    disclaimer: "Legal Disclaimer: BasedVector provides analytical data only. Not financial advice. Trading involves high risk.",
                    search: "Search Assets...",
                    showFavs: "Show Favorites",
                    showAll: "Show All Assets",
                    price: "Current Market Price",
                    vwap: "Avg. Purchase Cost (VWAP 365D)",
                    diff: "Distance from Avg. (Yearly Basis)",
                    rsi: "RSI (14)",
                    macd: "MACD",
                    signal: "SIGNAL",
                    close: "Close",
                    "STRONG BUY": "STRONG BUY", "BUY": "BUY", "NEUTRAL": "NEUTRAL", "SELL": "SELL", "STRONG SELL": "STRONG SELL"
                },
                tr: {
                    disclaimer: "Yasal Uyarı: BasedVector yalnızca analitik veri sağlar. Yatırım tavsiyesi değildir. Kripto ticareti yüksek risk içerir.",
                    search: "Varlık Ara...",
                    showFavs: "Favorileri Göster",
                    showAll: "Hepsini Göster",
                    price: "Güncel Piyasa Fiyatı",
                    vwap: "Ort. Satın Alma Maliyeti (VWAP 365G)",
                    diff: "Ortalamadan Uzaklık (Yıllık Bazda)",
                    rsi: "RSI (14)",
                    macd: "MACD",
                    signal: "SİNYAL",
                    close: "Kapat",
                    "STRONG BUY": "GÜÇLÜ AL", "BUY": "AL", "NEUTRAL": "NÖTR", "SELL": "SAT", "STRONG SELL": "GÜÇLÜ SAT"
                },
                zh: {
                    disclaimer: "法律声明：BasedVector 仅提供分析数据。不构成投资建议。加密货币交易具有高风险。",
                    search: "搜索资产...",
                    showFavs: "显示收藏夹",
                    showAll: "显示全部",
                    price: "当前市场价格",
                    vwap: "平均购买成本 (VWAP 365D)",
                    diff: "距均线的距离 (年度基数)",
                    rsi: "相对强弱指数 (14)",
                    macd: "指数平滑移动平均线",
                    signal: "信号",
                    close: "关闭",
                    "STRONG BUY": "强力买入", "BUY": "买入", "NEUTRAL": "中性", "SELL": "卖出", "STRONG SELL": "强力卖出"
                }
            };

            let currentLang = 'en';
            let favorites = JSON.parse(localStorage.getItem('favs')) || [];
            let showingFavsOnly = false;

            function changeLang(lang) {
                currentLang = lang;
                document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
                document.getElementById('btn-' + lang).classList.add('active');
                document.getElementById('disclaimer').innerText = translations[lang].disclaimer;
                document.getElementById('search-input').placeholder = translations[lang].search;
                document.getElementById('fav-filter-btn').innerText = showingFavsOnly ? translations[lang].showAll : translations[lang].showFavs;
                document.getElementById('close-modal-btn').innerText = translations[lang].close;
            }

            function openModal(encodedData) {
                const data = JSON.parse(atob(encodedData));
                const t = translations[currentLang];
                const diffColor = parseFloat(data.diff) >= 0 ? '#4ade80' : '#f87171';
                
                document.getElementById('m-title').innerText = data.symbol;
                document.getElementById('m-body').innerHTML = `
                    <div class="p-4 bg-slate-950 rounded-xl border border-slate-800">
                        <div class="text-slate-500 text-[10px] mb-1 uppercase font-bold tracking-wider">${t.price}</div>
                        <div class="font-mono text-2xl font-bold text-white">$${data.price}</div>
                    </div>
                    <div class="grid grid-cols-1 gap-3">
                        <div class="p-4 bg-slate-950 rounded-xl border border-slate-800">
                            <div class="text-slate-500 text-[10px] mb-1 uppercase font-bold tracking-wider">${t.vwap}</div>
                            <div class="font-mono text-xl font-bold text-sky-400">$${data.vwap}</div>
                        </div>
                        <div class="p-4 bg-slate-950 rounded-xl border border-slate-800">
                            <div class="text-slate-500 text-[10px] mb-1 uppercase font-bold tracking-wider">${t.diff}</div>
                            <div class="font-mono text-xl font-bold" style="color:${diffColor}">${data.diff}%</div>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 gap-3 pt-2">
                        <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                            <div class="text-slate-500 text-[10px] mb-1">${t.rsi}</div>
                            <div class="font-bold text-lg">${data.rsi}</div>
                        </div>
                        <div class="bg-slate-950 p-3 rounded-xl border border-slate-800 text-center">
                            <div class="text-slate-500 text-[10px] mb-1">${t.macd}</div>
                            <div class="font-bold text-lg">${data.macd}</div>
                        </div>
                    </div>
                    <div class="mt-4 text-center py-2 rounded-lg font-black tracking-widest text-sm" style="background-color:${data.color}">
                        ${t.signal}: ${t[data.signal_type]}
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
                document.getElementById('fav-filter-btn').innerText = showingFavsOnly ? translations[currentLang].showAll : translations[currentLang].showFavs;
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
