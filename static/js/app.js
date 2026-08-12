let currentSymbol = "XAUUSD";
let chartWidget = null;

document.addEventListener("DOMContentLoaded", () => {
    fetchConfig();
    fetchStatus();
    fetchLogs();
    fetchLatestAnalysis();

    setInterval(fetchStatus, 3000);
    setInterval(fetchLogs, 3000);
    setInterval(fetchLatestAnalysis, 5000);
});

async function fetchConfig() {
    try {
        const response = await fetch("/api/config");
        const data = await response.json();
        
        // Populate Symbol Select Dropdown
        const select = document.getElementById("symbol-select");
        if (select && data.symbols) {
            select.innerHTML = "";
            data.symbols.forEach(sym => {
                const opt = document.createElement("option");
                opt.value = sym;
                opt.text = sym;
                select.appendChild(opt);
            });
            if (data.symbols.length > 0) {
                currentSymbol = data.symbols[0];
                select.value = currentSymbol;
            }
        }
        initTradingViewChart(currentSymbol);
    } catch (err) {
        console.error("Config fetch error:", err);
    }
}

function switchChartSymbol() {
    const select = document.getElementById("symbol-select");
    if (select) {
        currentSymbol = select.value;
        initTradingViewChart(currentSymbol);
        fetchLatestAnalysis();
    }
}

function initTradingViewChart(symbol) {
    if (typeof TradingView === "undefined") return;
    const tvSymbol = symbol.startsWith("XAU") ? "OANDA:XAUUSD" : (symbol.includes(":") ? symbol : "FX:" + symbol);
    
    document.getElementById("tradingview-chart-box").innerHTML = "";
    new TradingView.widget({
        "autosize": true,
        "symbol": tvSymbol,
        "interval": "5",
        "timezone": "Etc/UTC",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#0b0f19",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "hide_legend": false,
        "save_image": false,
        "container_id": "tradingview-chart-box"
    });
}

async function fetchStatus() {
    try {
        const response = await fetch("/api/status");
        const data = await response.json();

        // Update MT5 Badge
        const mt5Badge = document.getElementById("badge-mt5");
        if (data.mt5_connected) {
            mt5Badge.className = "status-pill online";
            mt5Badge.innerHTML = '<i class="fa-solid fa-circle"></i> CONNECTED';
        } else {
            mt5Badge.className = "status-pill offline";
            mt5Badge.innerHTML = '<i class="fa-solid fa-circle"></i> DISCONNECTED';
        }

        // Update Bot Badge
        const botBadge = document.getElementById("badge-bot");
        const btnStart = document.getElementById("btn-start");
        const btnStop = document.getElementById("btn-stop");

        if (data.bot_running) {
            botBadge.className = "status-pill running";
            botBadge.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> SCALPER 90% ACTIVE';
            btnStart.disabled = true;
            btnStop.disabled = false;
        } else {
            botBadge.className = "status-pill stopped";
            botBadge.innerHTML = '<i class="fa-solid fa-circle"></i> STOPPED';
            btnStart.disabled = false;
            btnStop.disabled = true;
        }

        // Update Account Info
        document.getElementById("stat-company").innerText = data.company || "-";
        document.getElementById("stat-login").innerText = data.login || "-";
        document.getElementById("stat-balance").innerText = `$${formatMoney(data.balance)}`;
        document.getElementById("stat-equity").innerText = `$${formatMoney(data.equity)}`;

        const floatEl = document.getElementById("stat-floating");
        const floatVal = data.floating_profit || 0;
        floatEl.innerText = `${floatVal >= 0 ? "+" : ""}$${formatMoney(floatVal)}`;
        floatEl.className = "stat-val " + (floatVal > 0 ? "profit-pos" : floatVal < 0 ? "profit-neg" : "profit-neutral");

        renderPositions(data.positions);
    } catch (err) {
        console.error("Status fetch error:", err);
    }
}

function renderPositions(positions) {
    const tbody = document.getElementById("pos-table-body");
    if (!tbody) return;

    if (!positions || positions.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted" style="padding: 1rem; text-align: center; color: var(--text-muted);">Tidak ada posisi terbuka saat ini.</td></tr>`;
        return;
    }

    tbody.innerHTML = "";
    positions.forEach(p => {
        const tr = document.createElement("tr");
        const pClass = p.profit > 0 ? "profit-pos" : p.profit < 0 ? "profit-neg" : "profit-neutral";
        const typeBadge = p.type === "BUY" ? "badge-buy" : "badge-sell";
        
        tr.innerHTML = `
            <td>#${p.ticket}</td>
            <td><strong>${p.symbol}</strong></td>
            <td><span class="${typeBadge}">${p.type}</span></td>
            <td>${p.volume}</td>
            <td>${p.price_open.toFixed(5)}</td>
            <td>${p.price_current.toFixed(5)}</td>
            <td>${p.sl ? p.sl.toFixed(5) : '-'}</td>
            <td>${p.tp ? p.tp.toFixed(5) : '-'}</td>
            <td class="${pClass}"><strong>${p.profit >= 0 ? "+" : ""}$${p.profit.toFixed(2)}</strong></td>
        `;
        tbody.appendChild(tr);
    });
}

function clearConsoleUI() {
    const consoleEl = document.getElementById("log-console");
    if (consoleEl) consoleEl.innerHTML = "";
}

async function fetchLogs() {
    try {
        const response = await fetch("/api/logs");
        const logs = await response.json();
        const consoleEl = document.getElementById("log-console");
        if (!consoleEl) return;

        consoleEl.innerHTML = "";
        logs.forEach(line => {
            const div = document.createElement("div");
            let cls = "log-line";
            if (line.includes("WARNING")) cls += " warning";
            if (line.includes("ERROR")) cls += " error";
            div.className = cls;
            div.innerText = line;
            consoleEl.appendChild(div);
        });
        consoleEl.scrollTop = consoleEl.scrollHeight;
    } catch (err) {
        console.error("Logs fetch error:", err);
    }
}

async function fetchLatestAnalysis() {
    try {
        const response = await fetch("/api/latest-ai-analysis");
        const data = await response.json();
        if (data && data[currentSymbol]) {
            renderAnalysisReport(data[currentSymbol]);
        }
    } catch (err) {
        console.error("Analysis fetch error:", err);
    }
}

function renderAnalysisReport(report) {
    const reportPanel = document.getElementById("ai-report-panel");
    if (!reportPanel) return;

    const rec = (report.recommendation || "HOLD").toUpperCase();
    let badgeCls = "badge-hold";
    if (rec === "BUY") badgeCls = "badge-buy";
    if (rec === "SELL") badgeCls = "badge-sell";

    // Update 3 Indicator Cards
    const sig = report.sig_info || {};
    
    // EMA Card
    const emaVal = document.getElementById("rule-ema-val");
    if (emaVal) {
        if (sig.buy_ema) {
            emaVal.innerHTML = '<span class="badge-buy">EMA 9 CROSSOVER (BUY)</span>';
        } else if (sig.sell_ema) {
            emaVal.innerHTML = '<span class="badge-sell">EMA 9 CROSSUNDER (SELL)</span>';
        } else {
            emaVal.innerHTML = '<span style="color: var(--text-muted);">No Crossover</span>';
        }
    }

    // RSI Card
    const rsiVal = document.getElementById("rule-rsi-val");
    if (rsiVal) {
        const rsiNum = sig.curr_rsi || 50;
        if (rsiNum > 50) {
            rsiVal.innerHTML = `<span class="badge-buy">RSI ${rsiNum} > 50 (PASS)</span>`;
        } else if (rsiNum < 50) {
            rsiVal.innerHTML = `<span class="badge-sell">RSI ${rsiNum} < 50 (PASS)</span>`;
        } else {
            rsiVal.innerHTML = `<span style="color: var(--text-muted);">RSI ${rsiNum} (Neutral)</span>`;
        }
    }

    // MACD Card
    const macdVal = document.getElementById("rule-macd-val");
    if (macdVal) {
        if (sig.buy_macd) {
            macdVal.innerHTML = '<span class="badge-buy">MACD Line > Signal (PASS)</span>';
        } else if (sig.sell_macd) {
            macdVal.innerHTML = '<span class="badge-sell">MACD Line < Signal (PASS)</span>';
        } else {
            macdVal.innerHTML = '<span style="color: var(--text-muted);">Neutral</span>';
        }
    }

    let htmlAnalysis = (report.analysis || "Belum ada rincian.")
        .replace(/\n/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    reportPanel.innerHTML = `
        <div style="display: flex; gap: 1rem; margin-bottom: 0.8rem; align-items: center;">
            <div>Rekomendasi Scalping 90%: <span class="${badgeCls}">${rec}</span></div>
            <div>Confidence Score: <strong>${report.confidence}%</strong></div>
            <div>Support: <strong>${report.support ? report.support.toFixed(5) : '-'}</strong></div>
            <div>Resistance: <strong>${report.resistance ? report.resistance.toFixed(5) : '-'}</strong></div>
        </div>
        <div style="background: rgba(0,0,0,0.3); padding: 0.75rem; border-radius: 6px; font-size: 0.85rem; line-height: 1.5;">
            ${htmlAnalysis}
        </div>
        <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.5rem;">Dianalisis pada: ${report.timestamp || '-'}</div>
    `;
}

async function runInstant90Analysis() {
    const btnText = document.getElementById("btn-analyze-text");
    if (btnText) btnText.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Menganalisis...';

    try {
        const response = await fetch("/api/ai-analysis-90", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ symbol: currentSymbol })
        });
        const result = await response.json();
        if (result.status === "success") {
            fetchLatestAnalysis();
        } else {
            alert("Gagal analisis: " + result.message);
        }
    } catch (err) {
        console.error("Instant 90 analysis error:", err);
    } finally {
        if (btnText) btnText.innerHTML = '<i class="fa-solid fa-rotate"></i> ⚡ Analisis Setup Instan';
    }
}

async function startScalper() {
    const res = await fetch("/api/start", { method: "POST" });
    const data = await res.json();
    fetchStatus();
}

async function stopScalper() {
    const res = await fetch("/api/stop", { method: "POST" });
    const data = await res.json();
    fetchStatus();
}

async function saveConfig() {
    const payload = {
        symbols: document.getElementById("cfg-symbols").value,
        timeframe: document.getElementById("cfg-timeframe").value,
        lot_size: document.getElementById("cfg-lot").value,
        sl_pips: document.getElementById("cfg-sl").value,
        tp_pips: document.getElementById("cfg-tp").value,
        ema_fast: document.getElementById("cfg-ema-fast").value,
        ema_slow: document.getElementById("cfg-ema-slow").value,
        rsi_period: document.getElementById("cfg-rsi").value,
        macd_fast: document.getElementById("cfg-macd-fast").value,
        macd_slow: document.getElementById("cfg-macd-slow").value,
        macd_signal: document.getElementById("cfg-macd-sig").value,
        loop_interval_seconds: document.getElementById("cfg-interval").value,
        min_confidence: document.getElementById("cfg-conf").value,
        groq_api_key: document.getElementById("cfg-groq-key").value,
        gemini_api_key: document.getElementById("cfg-gemini-key").value,
        magic_number: document.getElementById("cfg-magic").value
    };

    const res = await fetch("/api/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (data.status === "success") {
        alert("Konfigurasi Scalping 90% berhasil disimpan!");
        fetchConfig();
    } else {
        alert("Gagal menyimpan: " + data.message);
    }
}

function formatMoney(val) {
    if (val === null || val === undefined) return "0.00";
    return val.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
