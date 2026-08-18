import threading
import time
import os
import json
import logging
from flask import Flask, render_template, jsonify, request
import MetaTrader5 as mt5

import bot

app = Flask(__name__)
logging.getLogger('werkzeug').setLevel(logging.ERROR)

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
bot_thread = None

def read_config():
    return bot.load_config()

def save_config(data):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving config.json: {e}")
        return False

def bot_loop():
    logging.info("Starting Scalping 90% Win Rate Bot Loop...")
    while bot.bot_running:
        config_data = read_config()
        if not config_data:
            logging.error("Configuration file error. Retrying in 10s...")
            time.sleep(10)
            continue

        try:
            if not mt5.initialize():
                logging.error(f"Failed to initialize MetaTrader 5: {mt5.last_error()}")
                time.sleep(10)
                continue
        except Exception as mt5_err:
            logging.error(f"MT5 Exception in bot loop: {mt5_err}")
            time.sleep(10)
            continue

        symbols = config_data.get("symbols", ["XAUUSD", "EURUSD", "GBPUSD"])
        timeframe_str = config_data.get("timeframe", "M5")
        lot_size = config_data.get("lot_size", 0.01)
        sl_pips = config_data.get("sl_pips", 15.0)
        tp_pips = config_data.get("tp_pips", 30.0)
        magic_number = config_data.get("magic_number", 20260900)
        loop_interval = config_data.get("loop_interval_seconds", 5)

        for symbol in symbols:
            if not bot.bot_running:
                break
            try:
                bot.run_bot_cycle(symbol, timeframe_str, lot_size, sl_pips, tp_pips, magic_number, config_data)
            except Exception as cycle_err:
                logging.error(f"Error during scalping 90% cycle for {symbol}: {cycle_err}")

        time.sleep(loop_interval)
    logging.info("Scalping 90% Win Rate Bot Loop Stopped.")

@app.route("/")
def index():
    config_data = read_config()
    return render_template("index.html", config=config_data)

@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    if request.method == "POST":
        new_config = request.json
        try:
            new_config["lot_size"] = float(new_config.get("lot_size", 0.01))
            new_config["sl_pips"] = float(new_config.get("sl_pips", 15.0))
            new_config["tp_pips"] = float(new_config.get("tp_pips", 30.0))
            new_config["magic_number"] = int(new_config.get("magic_number", 20260900))
            new_config["ema_fast"] = int(new_config.get("ema_fast", 9))
            new_config["ema_slow"] = int(new_config.get("ema_slow", 21))
            new_config["rsi_period"] = int(new_config.get("rsi_period", 14))
            new_config["macd_fast"] = int(new_config.get("macd_fast", 12))
            new_config["macd_slow"] = int(new_config.get("macd_slow", 26))
            new_config["macd_signal"] = int(new_config.get("macd_signal", 9))
            new_config["loop_interval_seconds"] = int(new_config.get("loop_interval_seconds", 5))
            new_config["min_confidence"] = int(new_config.get("min_confidence", 70))
            
            if "symbols" in new_config and isinstance(new_config["symbols"], str):
                new_config["symbols"] = [s.strip().upper() for s in new_config["symbols"].split(",") if s.strip()]
        except (ValueError, TypeError, KeyError) as e:
            return jsonify({"status": "error", "message": f"Invalid configuration: {e}"}), 400

        if save_config(new_config):
            return jsonify({"status": "success", "message": "Konfigurasi Scalping 90% berhasil disimpan."})
        else:
            return jsonify({"status": "error", "message": "Gagal menyimpan konfigurasi."}), 500
            
    return jsonify(read_config())

@app.route("/api/start", methods=["POST"])
def api_start():
    global bot_thread
    if not bot.bot_running:
        bot.bot_running = True
        bot_thread = threading.Thread(target=bot_loop, daemon=True)
        bot_thread.start()
        return jsonify({"status": "success", "message": "Bot Scalping 90% Win Rate berhasil dijalankan."})
    return jsonify({"status": "warning", "message": "Bot sudah berjalan."})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    if bot.bot_running:
        bot.bot_running = False
        return jsonify({"status": "success", "message": "Bot Scalping 90% berhasil dihentikan."})
    return jsonify({"status": "warning", "message": "Bot sudah berhenti."})

@app.route("/api/status", methods=["GET"])
def api_status():
    status = {
        "bot_running": bot.bot_running,
        "mt5_connected": False,
        "login": "-",
        "company": "-",
        "balance": 0.0,
        "equity": 0.0,
        "floating_profit": 0.0,
        "positions": []
    }
    
    try:
        is_initialized = mt5.initialize()
    except Exception:
        is_initialized = False

    if is_initialized:
        status["mt5_connected"] = True
        acc = mt5.account_info()
        if acc:
            status["login"] = acc.login
            status["company"] = acc.company
            status["balance"] = acc.balance
            status["equity"] = acc.equity
            status["floating_profit"] = acc.profit

        config_data = read_config()
        magic_number = config_data.get("magic_number", 20260900)
        positions = mt5.positions_get(magic=magic_number)
        if positions:
            pos_list = []
            for p in positions:
                pos_list.append({
                    "ticket": p.ticket,
                    "symbol": p.symbol,
                    "type": "BUY" if p.type == mt5.POSITION_TYPE_BUY else "SELL",
                    "volume": p.volume,
                    "price_open": p.price_open,
                    "price_current": p.price_current,
                    "sl": p.sl,
                    "tp": p.tp,
                    "profit": p.profit
                })
            status["positions"] = pos_list
            
    return jsonify(status)

@app.route("/api/logs", methods=["GET"])
def api_logs():
    return jsonify(list(bot.log_history))

@app.route("/api/latest-ai-analysis", methods=["GET"])
def api_latest_ai_analysis():
    return jsonify(bot.load_latest_ai_results())

@app.route("/api/ai-analysis-90", methods=["POST"])
def api_ai_analysis_90():
    config_data = read_config()
    symbol = request.json.get("symbol", "XAUUSD") if request.is_json else "XAUUSD"
    timeframe = config_data.get("timeframe", "M5")
    
    try:
        if not mt5.initialize():
            return jsonify({"status": "error", "message": "Gagal terhubung ke MT5 terminal."}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

    result = bot.run_ai_90_scalping_analysis(symbol, timeframe, config_data)
    if result["status"] == "success":
        clean_result = json.loads(json.dumps(result, default=bot.json_serialize_helper))
        latest_results = bot.load_latest_ai_results()
        latest_results[symbol] = {
            "recommendation": clean_result["recommendation"],
            "confidence": clean_result["confidence"],
            "support": clean_result["support"],
            "resistance": clean_result["resistance"],
            "analysis": clean_result["analysis"],
            "sig_info": clean_result.get("sig_info", {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        bot.save_latest_ai_results(latest_results)
        return jsonify({"status": "success", "data": clean_result})
    return jsonify({"status": "error", "message": result.get("message", "Analisis gagal. Silakan coba lagi.")}), 500

if __name__ == "__main__":
    print("Starting Scalping 90% Win Rate Bot on Port 5006...")
    app.run(host="0.0.0.0", port=5006, debug=False, use_reloader=False)
