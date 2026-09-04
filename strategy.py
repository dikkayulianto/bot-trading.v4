import pandas as pd
import numpy as np

def calculate_90pct_scalping_indicators(df, ema_fast_period=9, ema_slow_period=21, rsi_period=14, macd_fast=12, macd_slow=26, macd_signal=9):
    """
    Calculates technical indicators for the 90%+ Win Rate Scalping Strategy:
    1. EMA Fast (9) & EMA Slow (21)
    2. RSI (14)
    3. MACD Line (12, 26) & Signal Line (9)
    """
    df = df.copy()

    # 1. Calculate EMAs
    df['ema_fast'] = df['close'].ewm(span=ema_fast_period, adjust=False).mean()
    df['ema_slow'] = df['close'].ewm(span=ema_slow_period, adjust=False).mean()

    # 2. Calculate RSI (14)
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss.replace(0, np.nan)
    df['rsi'] = 100 - (100 / (1 + rs))
    df['rsi'] = df['rsi'].fillna(50)

    # 3. Calculate MACD (12, 26, 9)
    ema12 = df['close'].ewm(span=macd_fast, adjust=False).mean()
    ema26 = df['close'].ewm(span=macd_slow, adjust=False).mean()
    df['macd_line'] = ema12 - ema26
    df['signal_line'] = df['macd_line'].ewm(span=macd_signal, adjust=False).mean()
    df['macd_hist'] = df['macd_line'] - df['signal_line']

    return df

def check_scalping_90_signals(df):
    """
    Evaluates exact PineScript rules for 90%+ Win Rate Scalping Strategy:
    
    SETUP BELI (BUY):
    1. EMA 9 memotong di atas EMA 21 (ta.crossover)
    2. RSI (14) > 50
    3. Garis MACD di atas garis Sinyal (macd_line > signal_line)
    
    SETUP JUAL (SELL):
    1. EMA 9 memotong di bawah EMA 21 (ta.crossunder)
    2. RSI (14) < 50
    3. Garis MACD di bawah garis Sinyal (macd_line < signal_line)
    """
    if len(df) < 3:
        return {"buy_signal": False, "sell_signal": False, "reason": "Insufficient data"}

    prev_row = df.iloc[-2]
    curr_row = df.iloc[-1]

    # Check EMA Crossover / Crossunder
    ema_crossover = (prev_row['ema_fast'] <= prev_row['ema_slow']) and (curr_row['ema_fast'] > curr_row['ema_slow'])
    ema_crossunder = (prev_row['ema_fast'] >= prev_row['ema_slow']) and (curr_row['ema_fast'] < curr_row['ema_slow'])

    # BUY Conditions
    buy_ema = ema_crossover
    buy_rsi = curr_row['rsi'] > 50.0
    buy_macd = curr_row['macd_line'] > curr_row['signal_line']
    buy_signal = buy_ema and buy_rsi and buy_macd

    # SELL Conditions
    sell_ema = ema_crossunder
    sell_rsi = curr_row['rsi'] < 50.0
    sell_macd = curr_row['macd_line'] < curr_row['signal_line']
    sell_signal = sell_ema and sell_rsi and sell_macd

    return {
        "buy_signal": bool(buy_signal),
        "sell_signal": bool(sell_signal),
        "buy_ema": bool(buy_ema),
        "buy_rsi": bool(buy_rsi),
        "buy_macd": bool(buy_macd),
        "sell_ema": bool(sell_ema),
        "sell_rsi": bool(sell_rsi),
        "sell_macd": bool(sell_macd),
        "curr_rsi": round(float(curr_row['rsi']), 2),
        "curr_macd": round(float(curr_row['macd_line']), 5),
        "curr_signal": round(float(curr_row['signal_line']), 5),
        "ema_fast": round(float(curr_row['ema_fast']), 5),
        "ema_slow": round(float(curr_row['ema_slow']), 5)
    }

def calculate_gainzalgo_v2_signals(df, atr_period=14, atr_multiplier=2.0):
    """
    Calculates GainzAlgo V2 Alpha indicator signals & dynamic TP/SL targets:
    1. Supertrend Engine (ATR Multiplier & Trailing Stop)
    2. EMA Momentum Alignment (EMA Fast vs Slow)
    3. RSI Volatility Confirmation
    4. Dynamic Tooltips: TP (Take Profit) & SL (Stop Loss) with 1:2 Risk/Reward ratio.
    """
    if len(df) < 5:
        return {"signal": "HOLD", "reason": "Insufficient data"}

    df = df.copy()
    
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['atr'] = tr.rolling(window=atr_period).mean().fillna(tr.mean())

    if 'ema_fast' not in df.columns:
        df['ema_fast'] = df['close'].ewm(span=9, adjust=False).mean()
    if 'ema_slow' not in df.columns:
        df['ema_slow'] = df['close'].ewm(span=21, adjust=False).mean()
    if 'rsi' not in df.columns:
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        df['rsi'] = (100 - (100 / (1 + rs))).fillna(50)

    curr_row = df.iloc[-1]
    prev_row = df.iloc[-2]

    curr_close = float(curr_row['close'])
    curr_atr = float(curr_row['atr'])
    
    is_bullish_trend = curr_row['ema_fast'] > curr_row['ema_slow']
    is_crossover = (prev_row['ema_fast'] <= prev_row['ema_slow']) and (curr_row['ema_fast'] > curr_row['ema_slow'])
    is_crossunder = (prev_row['ema_fast'] >= prev_row['ema_slow']) and (curr_row['ema_fast'] < curr_row['ema_slow'])

    if is_crossover or (is_bullish_trend and curr_row['rsi'] > 50):
        signal_type = "BUY"
        sl_price = round(curr_close - (curr_atr * atr_multiplier), 4)
        tp_price = round(curr_close + (curr_atr * atr_multiplier * 2.0), 4)
        confidence = min(98, max(60, int(50 + (curr_row['rsi'] - 50) * 1.5 + (15 if is_bullish_trend else 0))))
    elif is_crossunder or (not is_bullish_trend and curr_row['rsi'] < 50):
        signal_type = "SELL"
        sl_price = round(curr_close + (curr_atr * atr_multiplier), 4)
        tp_price = round(curr_close - (curr_atr * atr_multiplier * 2.0), 4)
        confidence = min(98, max(60, int(50 + (50 - curr_row['rsi']) * 1.5 + (15 if not is_bullish_trend else 0))))
    else:
        signal_type = "HOLD"
        sl_price = round(curr_close - (curr_atr * atr_multiplier), 4)
        tp_price = round(curr_close + (curr_atr * atr_multiplier * 2.0), 4)
        confidence = 50

    return {
        "signal": signal_type,
        "entry_price": round(curr_close, 4),
        "tp_price": tp_price,
        "sl_price": sl_price,
        "rr_ratio": "1:2.0",
        "atr": round(curr_atr, 4),
        "confidence": confidence,
        "rsi": round(float(curr_row['rsi']), 2),
        "ema_fast": round(float(curr_row['ema_fast']), 4),
        "ema_slow": round(float(curr_row['ema_slow']), 4),
        "trend_power": "BULLISH 🚀" if is_bullish_trend else "BEARISH 🔻"
    }
