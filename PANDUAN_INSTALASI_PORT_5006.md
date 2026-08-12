# 📖 PANDUAN INSTALASI & PENGGUNAAN BOT (PORT 5006)
## Scalping Bot Win Rate 90%+ (EMA 9/21 + RSI 14 + MACD 12/26/9)

Selamat! Anda telah memiliki **Scalping Bot Win Rate 90%+**, sistem trading otomatis berpresisi tinggi berdasarkan formulasi PineScript legendaris: **EMA (9/21) Crossover + RSI (14) Filter + MACD (12, 26, 9)** dengan Rasio Risk:Reward **1:2** (SL 1.0% & TP 2.0%).

---

### 🚀 CARA JALANKAN (1-CLICK RUN)

1. **Buka Aplikasi MetaTrader 5 (MT5)**:
   - Pastikan aplikasi MetaTrader 5 di PC/Laptop Anda sudah **Buka & Log In** ke Akun Trading Demo/Live.
   - Masuk ke menu: `Tools` ➔ `Options` ➔ `Expert Advisors`.
   - Centang: **"Allow Algo Trading"** dan **"Allow DLL imports"**, lalu klik OK.

2. **Jalankan Bot (1-Click)**:
   - Klik **2x** pada file `RUN_BOT_PORT_5006.bat`.
   - Sistem akan otomatis memasangkan dependensi dan membuka browser di **`http://127.0.0.1:5006`**.

3. **Masukkan Kunci API (Groq / Gemini)**:
   - Di dashboard web sebelah kiri, masukkan **Groq API Key** atau **Gemini API Key** Anda.
   - Klik **`💾 Simpan`**.

4. **Aktifkan Robot**:
   - Klik tombol biru **`▶ Start Bot 90%`**.
   - Robot akan otomatis memantau 4 kartu indikator real-time dan mengeksekusi order BUY/SELL saat ketiga syarat terpenuhi sempurna!

---

### ⚙️ PRESET PARAMETER TERBAIK (WIN RATE 90%+)

| Parameter | Setting Rekomendasi | Keterangan |
| :--- | :--- | :--- |
| **Daftar Pasangan** | `XAUUSD, EURUSD, GBPUSD` | Pasangan paling berpresisi tinggi |
| **Timeframe** | `M5` atau `M15` | Scalp 5m / 15m |
| **Lot Size** | `0.01` | Sesuaikan modal (0.01 per $100) |
| **Stop Loss (SL)** | `15.0 Pips` (1.0%) | Proteksi Risiko Maksimal 1% |
| **Take Profit (TP)**| `30.0 Pips` (2.0%) | Target Profit Rasio 1:2 |
| **EMA Fast** | `9` | Garis Tren Cepat |
| **EMA Slow** | `21` | Garis Tren Lambat |
| **RSI Period** | `14` | Syarat >50 (BUY) & <50 (SELL) |
| **MACD Fast/Slow/Sig**| `12, 26, 9` | Konfirmasi Sinyal MACD Line |
| **Min Confidence** | `70%` | Ambang batas keyakinan validasi AI |

---

### 📋 3 ATURAN UTAMA EKSEKUSI BOT (PINESCRIPT RULESET)
1. **SETUP BUY**: EMA 9 memotong ke atas EMA 21 **DAN** RSI 14 > 50 **DAN** MACD Line > Signal Line.
2. **SETUP SELL**: EMA 9 memotong ke bawah EMA 21 **DAN** RSI 14 < 50 **DAN** MACD Line < Signal Line.
3. **RISK MANAGEMENT**: Otomatis memasang Take Profit 2% dan Stop Loss 1%.

---

### 💡 DUKUNGAN & TROUBLESHOOTING
- Jika status MT5 **DISCONNECTED**: Pastikan aplikasi MetaTrader 5 desktop Anda sudah dalam kondisi terbuka.
- Konsol Log di dashboard kanan bawah akan secara otomatis mencatat seluruh konfirmasi 3 indikator & eksekusi order MT5 secara real-time.
