@echo off
title Scalping 90% Win Rate Bot - Port 5006
color 0B
echo =======================================================================
echo         SCALPING 90%+ WIN RATE BOT (PORT 5006) 1-CLICK RUN
echo =======================================================================
echo.
echo [1/3] Memeriksa & Menginstall Dependensi Python...
python -m pip install --quiet flask requests MetaTrader5 pandas scikit-learn xgboost

echo.
echo [2/3] Membuka Dashboard Web di Browser (http://127.0.0.1:5006)...
start http://127.0.0.1:5006

echo.
echo [3/3] Menjalankan Server Bot Trading Port 5006...
echo -----------------------------------------------------------------------
python app.py
pause
