/**
 * Dashboard.js
 * Optimized for dual-table rendering (14-column Diff vs 6-column Hedge)
 */

let chart;
let mainLine;
let currentLine;
let socket;

document.addEventListener("DOMContentLoaded", () => {
    const chartElement = document.getElementById("chart-container");
    if (chartElement) {
        chart = LightweightCharts.createChart(chartElement, {
            width: chartElement.clientWidth,
            height: chartElement.clientHeight,
            layout: { background: { color: "#131722" }, textColor: "#d1d4dc" },
            grid: {
                vertLines: { color: "#1e222d" },
                horzLines: { color: "#1e222d" },
            },
            timeScale: { timeVisible: true, secondsVisible: true },
        });
        mainLine = chart.addLineSeries({ color: "#9c27b0", title: "Baseline" });
        currentLine = chart.addLineSeries({
            color: "#ff9800",
            title: "Total Diff",
        });
    }

    socket = new WebSocket(`ws://${window.location.host}/ws`);
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "UPDATE") {
            // FIX: Map incoming data to separate table handlers
            renderDashboard(data.diff_rows || [], data.hedge_rows || []);
        }
    };
});

function renderDashboard(diffRows, hedgeRows) {
    const now = Math.floor(Date.now() / 1000);

    // --- 1. Render DIFF TABLE (14 Columns) ---
    let diffHtml = "";
    let sCeLtp = 0,
        sPrCe = 0,
        sPrPe = 0,
        sPeLtp = 0;

    diffRows.forEach((row) => {
        sCeLtp += row.curr_ce;
        sPrCe += row.prev_ce;
        sPrPe += row.prev_pe;
        sPeLtp += row.curr_pe;

        diffHtml += `
      <tr>
        <td class="cb-cell"><input type="checkbox"></td>
        <td class="${getColorClass(row.total_diff)}">${row.total_diff.toFixed(2)}</td>
        <td class="${getColorClass(row.ce_diff_pct)}">${row.ce_diff_pct.toFixed(2)}</td>
        <td class="${getColorClass(row.ce_diff)}">${row.ce_diff.toFixed(2)}</td>
        <td>${row.curr_ce.toFixed(2)}</td>
        <td>${row.prev_ce.toFixed(2)}</td>
        <td>${row.ce_strike}</td>
        <td>${row.pe_strike}</td>
        <td>${row.prev_pe.toFixed(2)}</td>
        <td>${row.curr_pe.toFixed(2)}</td>
        <td class="${getColorClass(row.pe_diff)}">${row.pe_diff.toFixed(2)}</td>
        <td class="${getColorClass(row.pe_diff_pct)}">${row.pe_diff_pct.toFixed(2)}</td>
        <td class="${getColorClass(row.total_diff_pct)}">${row.total_diff_pct}</td>
        <td class="cb-cell"><input type="checkbox"></td>
      </tr>`;
    });

    // Sticky Totals Row for Diff Table
    const diffFooter = `
    <tr class="footer-row">
    <td colspan="4"></td>
      <td>${sCeLtp.toFixed(2)}</td><td>${sPrCe.toFixed(2)}</td>
      <td colspan="2" style="text-align:center; font-weight:bold;">TOTALS</td>
      <td>${sPrPe.toFixed(2)}</td><td>${sPeLtp.toFixed(2)}</td>
      <td colspan="4"></td>
    </tr>`;

    const diffBody = document.getElementById("diffBody");
    if (diffBody) diffBody.innerHTML = diffHtml + diffFooter;

    // --- 2. Render HEDGE TABLE (6 Columns) ---
    let hedgeHtml = "";
    hedgeRows.forEach((row) => {
        hedgeHtml += `
      <tr>
        <td class="cb-cell"><input type="checkbox"></td>
        <td>${row.curr_ce.toFixed(2)}</td>
        <td>${row.ce_strike}</td>
        <td>${row.pe_strike}</td>
        <td>${row.curr_pe.toFixed(2)}</td>
        <td class="cb-cell"><input type="checkbox"></td>
      </tr>`;
    });

    const hedgeBody = document.getElementById("hedgeBody");
    if (hedgeBody) hedgeBody.innerHTML = hedgeHtml;

    // --- 3. Update Chart ---
    if (currentLine) currentLine.update({ time: now, value: sCeLtp + sPeLtp });
    if (mainLine) mainLine.update({ time: now, value: sPrCe + sPrPe });
}

function getColorClass(val) {
    return val < 0 ? "neg" : "pos";
}

// Logic for update buttons (Preserving unified symbol truth)
function updateDiff() {
    sendSub("DIFF", "base-strike", "num-strikes", "diff-call-put");
}
function updateHedge() {
    sendSub(
        "HEDGE",
        "hedge-base-strike",
        "hedge-num-strikes",
        "hedge-call-put",
    );
}

function sendSub(ns, baseId, qtyId, radioName) {
    const sym = document.getElementById("symbol-select").value;
    const base = document.getElementById(baseId).value;
    const qty = document.getElementById(qtyId).value;
    const type = document.querySelector(
        `input[name="${radioName}"]:checked`,
    ).value;

    if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(
            JSON.stringify({
                action: "SUBSCRIBE",
                namespace: ns,
                symbol: sym,
                base_strike: parseInt(base),
                num_strikes: parseInt(qty),
                option_type: type,
            }),
        );
    }
}

/**
 * Unified subscription updater
 * @param {string} side - Must be 'main' or 'hedge' to match HTML IDs
 */
async function updateSubscription(side) {
    // Collecting values manually using the side as the ID prefix
    const payload = {
        side: side,
        base_expiry: document.getElementById("symbol-select").value,
        ce_start: document.getElementById(`${side}-call-base`).value,
        pe_start: document.getElementById(`${side}-put-base`).value,
        num_of_strikes: document.getElementById(`${side}-num`).value, // Assuming same count for both
    };

    try {
        const response = await fetch("/update-subscription", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        const result = await response.json();
        if (result.status === "success") {
            console.log(`Successfully updated ${side} tokens.`);
        }
    } catch (error) {
        console.error("Subscription update failed:", error);
    }
}
