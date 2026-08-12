import time
import os
import logging
import json
import collections
import requests
import MetaTrader5 as mt5
import pandas as pd

import strategy

# Configure in-memory log queue for Web UI console
log_history = collections.deque(maxlen=200)

class MemoryHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = record.getMessage()
            # Ignore HTTP noise and polling routine logs
            if any(ignore in msg for ignore in ["GET /api", "POST /api", "Debugger", "running on http", "127.0.0.1", "is still forming", "Press CTRL+C"]):
                return
            log_entry = self.format(record)
            log_history.append(log_entry)
        except Exception:
            self.handleError(record)

# Configure logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# File handler
file_handler = logging.FileHandler("bot_scalping_90.log", encoding="utf-8")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Memory handler
mem_handler = MemoryHandler()
mem_handler.setFormatter(formatter)
logger.addHandler(mem_handler)

TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1
}

bot_running = False
last_processed_candles = {}
ANALYSIS_JSON_FILE = os.path.join(os.path.dirname(__file__), "latest_ai_analysis.json")

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Failed to load config.json: {e}")
        return None

def load_latest_ai_results():
    if os.path.exists(ANALYSIS_JSON_FILE):
        try:
            with open(ANALYSIS_JSON_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def json_serialize_helper(obj):
    if hasattr(obj, 'item'):
        return obj.item()
    if isinstance(obj, (bool, int, float, str)):
        return obj
    return str(obj)

def save_latest_ai_results(data):
    try:
        with open(ANALYSIS_JSON_FILE, "w") as f:
            json.dump(data, f, indent=2, default=json_serialize_helper)
    except Exception as e:
        logging.error(f"Failed to save latest AI analysis: {e}")

def get_historical_data(symbol, timeframe, count=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

def get_filling_type(symbol_info):
    filling_mode = symbol_info.filling_mode
    if filling_mode & 1:  # FOK
        return mt5.ORDER_FILLING_FOK
    elif filling_mode & 2:  # IOC
        return mt5.ORDER_FILLING_IOC
    return mt5.ORDER_FILLING_RETURN

def get_groq_scalping_analysis(symbol, timeframe_str, groq_api_key, config_data, sig_info):
    """
    Calls Groq AI (Llama 3.3 70B) to validate the 90%+ Win Rate Scalping Signal.
    """
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        mt5.symbol_select(symbol, True)
        symbol_info = mt5.symbol_info(symbol)
        
    if symbol_info is None:
        return {"status": "error", "message": f"Simbol {symbol} tidak ditemukan."}

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        return {"status": "error", "message": f"Gagal mengambil harga tick {symbol}."}

    mt5_tf = TIMEFRAME_MAP.get(timeframe_str, mt5.TIMEFRAME_M5)
    df = get_historical_data(symbol, mt5_tf, count=60)
    if df is None or len(df) < 20:
        return {"status": "error", "message": f"Data historis {symbol} tidak cukup."}

    df = strategy.calculate_90pct_scalping_indicators(
        df, 
        config_data.get("ema_fast", 9), 
        config_data.get("ema_slow", 21), 
        config_data.get("rsi_period", 14),
        config_data.get("macd_fast", 12),
        config_data.get("macd_slow", 26),
        config_data.get("macd_signal", 9)
    )

    curr_row = df.iloc[-1]
    
    candles_summary = []
    for _, row in df.tail(10).iterrows():
        candles_summary.append(
            f"Time: {row['time'].strftime('%Y-%m-%d %H:%M')}, O: {row['open']:.5f}, H: {row['high']:.5f}, L: {row['low']:.5f}, C: {row['close']:.5f}, Vol: {row['tick_volume']}"
        )
    candles_summary_str = "\n".join(candles_summary)

    prompt = f"""
    Anda adalah analis trading profesional berpengalaman tinggi yang memverifikasi "Strategi Scalping Win Rate 90%+".
    Tolong lakukan verifikasi keputusan trading pada {symbol} timeframe {timeframe_str} berdasarkan aturan strategi berikut:
    
    ATURAN STRATEGI SCALPING 90%:
    - SETUP BUY: EMA 9 crossover EMA 21 AND RSI(14) > 50 AND MACD Line > Signal Line.
    - SETUP SELL: EMA 9 crossunder EMA 21 AND RSI(14) < 50 AND MACD Line < Signal Line.
    - Risk Reward Ratio: 1:2 (SL 1.0% / TP 2.0%)
    
    DATA HARGA & INDIKATOR SAAT INI:
    - Bid={tick.bid:.5f}, Ask={tick.ask:.5f}
    - Close={curr_row['close']:.5f}
    - EMA 9: {curr_row['ema_fast']:.5f} | EMA 21: {curr_row['ema_slow']:.5f}
    - RSI 14: {curr_row['rsi']:.2f} (Syarat >50 untuk BUY, <50 untuk SELL)
    - MACD Line: {curr_row['macd_line']:.5f} | Signal Line: {curr_row['signal_line']:.5f}
    - Signal Engine Result: BUY={sig_info['buy_signal']}, SELL={sig_info['sell_signal']}
    
    Histori 10 Lilin Terakhir:
    {candles_summary_str}
    
    Evaluasi keakuratan setup di atas. Berikan rekomendasi akhir (BUY, SELL, atau HOLD) beserta skor kepercayaan (0-100%).
    
    HARUS membalas HANYA dalam format JSON berikut tanpa markdown tambahan:
    {{
      "recommendation": "BUY" atau "SELL" atau "HOLD",
      "confidence": nilai integer antara 0 hingga 100,
      "support": nilai float support terdekat,
      "resistance": nilai float resistance terdekat,
      "analysis": "Laporan analisis validasi strategi Scalping 90% dalam Bahasa Indonesia. Gunakan tag HTML seperti <h3>, <p>, <ul>, <li>."
    }}
    """

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {groq_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "response_format": {"type": "json_object"},
        "temperature": 0.1
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        if response.status_code != 200:
            payload["model"] = "llama-3.1-8b-instant"
            response = requests.post(url, headers=headers, json=payload, timeout=20)
            if response.status_code != 200:
                return {"status": "error", "message": f"Groq API HTTP {response.status_code}"}
                
        response_data = response.json()
        ai_text = response_data['choices'][0]['message']['content']
        ai_json = json.loads(ai_text)
        
        return {
            "status": "success",
            "recommendation": ai_json.get("recommendation", "HOLD").upper(),
            "confidence": int(ai_json.get("confidence", 50)),
            "support": float(ai_json.get("support", tick.bid)),
            "resistance": float(ai_json.get("resistance", tick.ask)),
            "analysis": ai_json.get("analysis", "Analisis Strategi Scalping 90% selesai.")
        }
    except Exception as e:
        return {"status": "error", "message": f"Groq Exception: {e}"}

def run_ai_90_scalping_analysis(symbol, timeframe_str, config_data):
    groq_api_key = config_data.get("groq_api_key", "").strip()
    
    mt5_tf = TIMEFRAME_MAP.get(timeframe_str, mt5.TIMEFRAME_M5)
    df = get_historical_data(symbol, mt5_tf, count=60)
    if df is None:
        return {"status": "error", "message": f"Gagal mengambil data {symbol}."}

    df = strategy.calculate_90pct_scalping_indicators(
        df, 
        config_data.get("ema_fast", 9), 
        config_data.get("ema_slow", 21), 
        config_data.get("rsi_period", 14),
        config_data.get("macd_fast", 12),
        config_data.get("macd_slow", 26),
        config_data.get("macd_signal", 9)
    )

    sig_info = strategy.check_scalping_90_signals(df)

    if groq_api_key:
        logging.info(f"Running Groq AI Scalping 90% Validation for {symbol}...")
        res = get_groq_scalping_analysis(symbol, timeframe_str, groq_api_key, config_data, sig_info)
        if res.get("status") == "success":
            res["sig_info"] = sig_info
            return res

    # Algorithmic fallback if Groq API key is missing
    rec = "HOLD"
    conf = 50
    if sig_info["buy_signal"]:
        rec = "BUY"
        conf = 90
    elif sig_info["sell_signal"]:
        rec = "SELL"
        conf = 90

    return {
        "status": "success",
        "recommendation": rec,
        "confidence": conf,
        "support": df.iloc[-1]['low'],
        "resistance": df.iloc[-1]['high'],
        "analysis": f"<h3>Analisis Algoritma Scalping 90%</h3><p>Signal Engine Result for {symbol}: <strong>{rec}</strong>.</p><ul><li>EMA 9 Crossover 21: {sig_info['buy_ema'] or sig_info['sell_ema']}</li><li>RSI (14) Filter: {sig_info['curr_rsi']}</li><li>MACD Signal: Line={sig_info['curr_macd']} vs Sig={sig_info['curr_signal']}</li></ul>",
        "sig_info": sig_info
    }

def has_same_direction_position(symbol, order_type, magic_number):
    positions = mt5.positions_get(symbol=symbol, magic=magic_number)
    if not positions:
        return False, None
    same_type = mt5.POSITION_TYPE_BUY if order_type == mt5.ORDER_TYPE_BUY else mt5.POSITION_TYPE_SELL
    for pos in positions:
        if pos.type == same_type:
            return True, pos.ticket
    return False, None

def close_opposite_positions(symbol, new_order_type, magic_number):
    positions = mt5.positions_get(symbol=symbol, magic=magic_number)
    if not positions:
        return
    opposite_type = mt5.POSITION_TYPE_SELL if new_order_type == mt5.ORDER_TYPE_BUY else mt5.POSITION_TYPE_BUY
    for pos in positions:
        if pos.type == opposite_type:
            logging.info(f"Closing opposite Scalping position {pos.ticket} on {symbol} before opening new deal.")
            close_request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "position": pos.ticket,
                "price": mt5.symbol_info_tick(symbol).bid if pos.type == mt5.POSITION_TYPE_BUY else mt5.symbol_info_tick(symbol).ask,
                "deviation": 20,
                "magic": magic_number,
                "comment": "Close opposite scalping 90",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": get_filling_type(mt5.symbol_info(symbol)),
            }
            mt5.order_send(close_request)

def execute_order(symbol, order_type, lot_size, sl_pips, tp_pips, magic_number):
    tick = mt5.symbol_info_tick(symbol)
    symbol_info = mt5.symbol_info(symbol)
    if tick is None or symbol_info is None:
        logging.error(f"Failed to get price ticks for Scalping order execution on {symbol}.")
        return False

    close_opposite_positions(symbol, order_type, magic_number)
    already_has_pos, existing_ticket = has_same_direction_position(symbol, order_type, magic_number)
    if already_has_pos:
        type_str = "BUY" if order_type == mt5.ORDER_TYPE_BUY else "SELL"
        logging.info(f"Posisi Scalping 90% {type_str} untuk {symbol} sudah terbuka (Ticket: {existing_ticket}). Melewati eksekusi ganda.")
        return False

    point = symbol_info.point
    digits = symbol_info.digits
    
    # Calculate SL and TP (Risk Reward 1:2 Ratio)
    pip_mult = 10 if digits in [3, 5] or symbol.startswith("XAU") else 1
    if order_type == mt5.ORDER_TYPE_BUY:
        price = tick.ask
        sl = price - (sl_pips * pip_mult * point) if sl_pips > 0 else 0.0
        tp = price + (tp_pips * pip_mult * point) if tp_pips > 0 else 0.0
    else:
        price = tick.bid
        sl = price + (sl_pips * pip_mult * point) if sl_pips > 0 else 0.0
        tp = price - (tp_pips * pip_mult * point) if tp_pips > 0 else 0.0

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot_size,
        "type": order_type,
        "price": price,
        "sl": round(sl, digits),
        "tp": round(tp, digits),
        "deviation": 20,
        "magic": magic_number,
        "comment": "Scalping 90% WinRate",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": get_filling_type(symbol_info),
    }

    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"Scalping 90% Order failed for {symbol}: retcode={result.retcode}, error={mt5.last_error()}")
        return False

    logging.info(f"Successfully placed Scalping 90% order {request['comment']} on {symbol}. Retcode: {result.retcode}")
    return True

import datetime

def verify_license(config_data):
    acc_info = mt5.account_info()
    if not acc_info:
        return False, "Gagal membaca data akun MT5."
        
    user_login = acc_info.login
    allowed_accounts = config_data.get("allowed_account_numbers", [])
    if allowed_accounts and len(allowed_accounts) > 0:
        if user_login not in allowed_accounts:
            return False, f"AKUN TERKUNCI: Nomor Akun MT5 ({user_login}) tidak terdaftar dalam lisensi sah!"

    expire_date_str = config_data.get("license_expire_date", "").strip()
    if expire_date_str:
        try:
            expire_date = datetime.datetime.strptime(expire_date_str, "%Y-%m-%d")
            today = datetime.datetime.now()
            if today > expire_date:
                return False, f"LISENSI KADALUARSA: Masa sewa lisensi bot telah berakhir pada {expire_date_str}!"
        except ValueError:
            pass

    return True, "LICENSE_VALID"

def run_bot_cycle(symbol, timeframe_str, lot_size, sl_pips, tp_pips, magic_number, config_data):
    global last_processed_candles

    valid, lic_msg = verify_license(config_data)
    if not valid:
        logging.error(f"SECURITY LOCK: {lic_msg}")
        return
        
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        mt5.symbol_select(symbol, True)
        symbol_info = mt5.symbol_info(symbol)
        
    if symbol_info is None:
        logging.error(f"Symbol {symbol} not found.")
        return

    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            logging.error(f"Failed to select symbol {symbol}.")
            return

    mt5_tf = TIMEFRAME_MAP.get(timeframe_str, mt5.TIMEFRAME_M5)
    df = get_historical_data(symbol, mt5_tf, count=60)
    if df is None or len(df) == 0:
        logging.error(f"No historical rates available for {symbol}.")
        return

    df = strategy.calculate_90pct_scalping_indicators(
        df, 
        config_data.get("ema_fast", 9), 
        config_data.get("ema_slow", 21), 
        config_data.get("rsi_period", 14),
        config_data.get("macd_fast", 12),
        config_data.get("macd_slow", 26),
        config_data.get("macd_signal", 9)
    )

    latest_candle_time = df.iloc[-1]['time'].strftime("%Y-%m-%d %H:%M:%S")
    is_new_candle = False
    if symbol not in last_processed_candles:
        last_processed_candles[symbol] = latest_candle_time
        logging.info(f"Scalping 90% - Initializing tracking for {symbol} at candle {latest_candle_time}. Waiting for next close.")
    elif latest_candle_time > last_processed_candles[symbol]:
        last_processed_candles[symbol] = latest_candle_time
        is_new_candle = True
        logging.info(f"Scalping 90% - New candle closed for {symbol} at {latest_candle_time}. Checking Setup 90%...")

    if is_new_candle:
        ai_res = run_ai_90_scalping_analysis(symbol, timeframe_str, config_data)
        if ai_res["status"] != "success":
            logging.error(f"Scalping 90% analysis engine failed for {symbol}: {ai_res.get('message')}")
            return
            
        ai_rec = ai_res["recommendation"]
        ai_conf = ai_res["confidence"]
        min_conf = config_data.get("min_confidence", 70)
        
        latest_results = load_latest_ai_results()
        latest_results[symbol] = {
            "recommendation": ai_rec,
            "confidence": ai_conf,
            "support": ai_res.get("support", 0.0),
            "resistance": ai_res.get("resistance", 0.0),
            "analysis": ai_res.get("analysis", ""),
            "sig_info": ai_res.get("sig_info", {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        save_latest_ai_results(latest_results)

        logging.info(f"Scalping 90% Recommendation for {symbol}: {ai_rec} (Confidence: {ai_conf}%, Min: {min_conf}%)")

        if ai_conf >= min_conf:
            if ai_rec == "BUY":
                execute_order(symbol, mt5.ORDER_TYPE_BUY, lot_size, sl_pips, tp_pips, magic_number)
            elif ai_rec == "SELL":
                execute_order(symbol, mt5.ORDER_TYPE_SELL, lot_size, sl_pips, tp_pips, magic_number)
        else:
            logging.info(f"Scalping 90% trade skipped due to confidence ({ai_conf}% < {min_conf}%).")
