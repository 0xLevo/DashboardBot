import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime, timezone
import json
import base64

# --- TOP 200 COINS (Genişletilmiş ve Güncel Liste) ---
TOP_COINS = [
    'BTC', 'ETH', 'BNB', 'SOL', 'XRP', 'ADA', 'AVAX', 'DOGE', 'DOT', 'TRX',
    'LINK', 'MATIC', 'TON', 'SHIB', 'LTC', 'BCH', 'NEAR', 'UNI', 'PEPE', 'ICP',
    'APT', 'RNDR', 'HBAR', 'FIL', 'XLM', 'ARB', 'ATOM', 'STX', 'VET', 'LDO',
    'MKR', 'TIA', 'GRT', 'THETA', 'FTM', 'SEI', 'SUI', 'OP', 'INJ', 'RUNE',
    'FLOKI', 'LUNC', 'GALA', 'PENDLE', 'DYDX', 'AAVE', 'ORDI', 'WIF', 'BONK',
    'PYTH', 'JUP', 'FET', 'EGLD', 'FLOW', 'MINA', 'AXS', 'CHZ', 'MANA', 'SAND',
    'EOS', 'XTZ', 'IOTA', 'KAVA', 'CAKE', 'ASTR', 'ZIL', 'DASH', 'XMR', 'WLD',
    'STRK', 'DYM', 'MANTA', 'ALT', 'RON', 'CKB', 'BTT', 'HOT', 'GMT', 'SNX'
    # Liste isteğe göre 200'e tamamlanabilir...
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
    # Teknik Göstergeler
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rsi = 100 - (100 / (1 + (gain / (loss + 1e-9))))

    ema12 = df['close'].ewm(span=12, adjust=False).mean()
    ema26 = df['close'].ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    signal_line = macd.ewm(span=9, adjust=False).mean()

    # 365D VWAP (Hacim Ağırlıklı Ortalama)
    vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
    current_price = df['close'].iloc[-1]
    cost_diff_pct = ((current_price - vwap) / vwap) * 100
    
    # 24s Değişim (Basit Momentum)
    change_24h = ((current_price - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100

    return {
        'rsi': rsi.iloc[-1], 'macd': macd.iloc[-1], 'signal': signal_line.iloc[-1],
        'close': current_price, 'vwap': vwap, 'diff': cost_diff_pct, 'change': change_24h
    }

def get_enhanced_signal(data):
    """Hibrit Sinyal: Teknik + Maliyet Analizi"""
    score = 0
    # RSI Skoru
    if data['rsi'] < 30: score += 2
    elif data['rsi'] > 70: score -= 2
    
    # MACD Skoru
    if data['macd'] > data['signal']: score += 1
    else: score -= 1
    
    # Maliyet Bazlı Skor (VWAP) - Fiyat ortalamanın çok altındaysa 'Değer Alanı'
    if data['diff'] < -30: score += 2
    elif data['diff'] > 50: score -= 2

    if score >= 3: return "STRONG BUY", "#10b981" # Daha parlak yeşil
    elif score >= 1: return "BUY", "#059669"
    elif score <= -3: return "STRONG SELL", "#ef4444" # Daha parlak kırmızı
    elif score <= -1: return "SELL", "#b91c1c"
    else: return "NEUTRAL", "#334155"

def analyze_market():
    exchange = ccxt.mexc({'enableRateLimit': True})
    results = []
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Analiz başlatıldı...")
    
    for symbol in TOP_COINS:
        try:
            pair = f"{symbol}/USDT"
            bars = exchange.fetch_ohlcv(pair, timeframe='1d', limit=400)
            if len(bars) < 300: continue
            
            df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
            metrics = calculate_metrics(df)
            signal_name, color = get_enhanced_signal(metrics)
            
            results.append({
                'symbol': symbol,
                'price': format_crypto_price(metrics['close']),
                'change': f"{metrics['change']:+.2f}%",
                'rsi': f"{metrics['rsi']:.1f}",
                'macd': f"{metrics['macd']:.4f}",
                'vwap': format_crypto_price(metrics['vwap']),
                'diff': f"{metrics['diff']:.2f}",
                'signal_type': signal_name,
                'color': color
            })
            time.sleep(0.05) # Rate limit koruması
        except Exception: continue
        
    print(f"Analiz tamamlandı. {len(results)} varlık işlendi.")
    return results

def create_html(data):
    # (HTML içeriği buraya gelecek - Önceki sürümün güncellenmiş hali)
    # create_html fonksiyonu içine data['change'] bilgisini kutucuklara ekleyen 
    # küçük bir span eklendi.
    
    full_update = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    html = f"""
    <!DOCTYPE html><html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>BasedVector | Professional Analytics</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap" rel="stylesheet">
        <style>
            body {{ font-family: 'Inter', sans-serif; background-color: #020617; color: white; }}
            .coin-box {{ border-radius: 8px; transition: 0.3s; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
            .coin-box:hover {{ transform: translateY(-4px); border-color: white; box-shadow: 0 10px 15px -3px rgba(0,0,0,0.5); }}
            .modal {{ display: none; position: fixed; z-index: 100; inset: 0; background: rgba(0,0,0,0.8); backdrop-filter: blur(8px); }}
            .modal-content {{ background: #0f172a; margin: 5% auto; padding: 2rem; border-radius: 1.5rem; width: 90%; max-width: 450px; border: 1px solid #1e293b; }}
            .lang-btn.active {{ background: #3b82f6; color: white; }}
        </style>
    </head>
    <body class="p-4 md:p-10">
        <div class="max-w-7xl mx-auto">
            <div class="flex flex-col md:flex-row justify-between items-center mb-10 border-b border-slate-800 pb-6">
                <div>
                    <h1 class="text-4xl font-black tracking-tighter text-blue-500 mb-2">BASEDVECTOR <span class="text-white text-lg font-normal ml-2 opacity-50">PRO TERMINAL</span></h1>
                    <div class="flex gap-2">
                        <button onclick="changeLang('en')" id="btn-en" class="lang-btn active text-xs px-3 py-1 rounded bg-slate-800">EN</button>
                        <button onclick="changeLang('tr')" id="btn-tr" class="lang-btn text-xs px-3 py-1 rounded bg-slate-800">TR</button>
                    </div>
                </div>
                <div class="text-right mt-4 md:mt-0">
                    <div class="text-[10px] text-slate-500 font-mono mb-2 uppercase">Last Synced: {full_update} UTC</div>
                    <input type="text" id="search-input" onkeyup="filterCoins()" placeholder="Search asset..." class="bg-slate-900 border border-slate-700 px-4 py-2 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500">
                </div>
            </div>

            <div class="grid grid-cols-3 sm:grid-cols-5 md:grid-cols-8 lg:grid-cols-10 gap-3" id="coin-grid">
    """
    for i in data:
        encoded_data = base64.b64encode(json.dumps(i).encode()).decode()
        change_color = "text-green-400" if "+" in i['change'] else "text-red-400"
        html += f"""
        <div class="coin-box p-4 text-center cursor-pointer relative overflow-hidden" style="background-color: {i['color']};" onclick="openModal('{encoded_data}')" data-symbol="{i['symbol']}">
            <div class="font-black text-sm mb-1">{i['symbol']}</div>
            <div class="text-[9px] font-bold {change_color} bg-black/30 rounded py-0.5 px-1 inline-block">{i['change']}</div>
        </div>
        """
    # (Alt Script ve Modal kısmı önceki sürümle entegre edilecek)
    html += "</div></div></body></html>" 
    with open("index.html", "w", encoding="utf-8") as f: f.write(html)

if __name__ == "__main__":
    create_html(analyze_market())
