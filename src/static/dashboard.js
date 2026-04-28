/**
 * Dashboard.js
 * Optimized for dual-table rendering (14-column Diff vs 6-column Hedge)
 */

let chart;
let mainLine;
let currentLine;
let socket;

document.addEventListener("DOMContentLoaded", function() {
    const chartElement = document.getElementById("chart-container");
    if (chartElement) {
        const mainToggle = document.getElementById("main-side-toggle");
        const hedgeToggle = document.getElementById("hedge-side-toggle");
        if (mainToggle) window.tableModes.main = mainToggle.checked ? 'SELL' : 'BUY';
        if (hedgeToggle) window.tableModes.hedge = hedgeToggle.checked ? 'SELL' : 'BUY';

        chart = LightweightCharts.createChart(chartElement, {
            width: chartElement.clientWidth,
            height: chartElement.clientHeight,
            layout: { background: { color: "#131722" }, textColor: "#d1d4dc" },
            grid: { vertLines: { color: "#1e222d" }, horzLines: { color: "#1e222d" } },
        });
        mainLine = chart.addLineSeries({ color: "#9c27b0", title: "Baseline" });
        currentLine = chart.addLineSeries({ color: "#ff9800", title: "Total Diff" });
    }

    socket = new WebSocket("ws://" + window.location.host + "/ws");
    socket.onopen = function() { updateConnectionStatus(true); };
    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        if (data.type === "UPDATE") {
            renderDashboard(data.diff_rows || [], data.hedge_rows || [], data.main_fresh || 0, data.hedge_fresh || 0);
        }
    };
    socket.onclose = function() { updateConnectionStatus(false); };

    // Resizable chart
    const resizeHandle = document.getElementById("resize-handle");
    const chartSection = document.getElementById("chart-section");
    const dashboardContainer = document.querySelector(".dashboard-container");
    
    if (resizeHandle && chartSection && dashboardContainer) {
        let isResizing = false;
        let startY = 0;
        let startChartHeight = 0;
        
        resizeHandle.addEventListener("mousedown", function(e) {
            isResizing = true;
            startY = e.clientY;
            startChartHeight = chartSection.offsetHeight;
            document.body.style.cursor = "ns-resize";
        });
        
        document.addEventListener("mousemove", function(e) {
            if (!isResizing) return;
            const deltaY = startY - e.clientY;
            const newChartHeight = Math.max(startChartHeight * 0.1, Math.min(startChartHeight * 0.8, startChartHeight + deltaY));
            chartSection.style.height = newChartHeight + "px";
            if (chart && chartSection.offsetHeight > 8) chart.resize(chartSection.offsetWidth, chartSection.offsetHeight - 8);
        });
        
        document.addEventListener("mouseup", function() {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = "";
            }
        });
    }
    
    window.addEventListener("resize", function() {
        const chartSection = document.getElementById("chart-section");
        if (chart && chartSection) {
            chart.resize(chartSection.offsetWidth, chartSection.offsetHeight - 8);
        }
    });
});

function updateConnectionStatus(connected) {
    const status = document.getElementById("ws-status");
    if (status) {
        status.className = connected ? "ws-status connected" : "ws-status disconnected";
    }
}

window.addEventListener("beforeunload", function() {
    if (socket) socket.close();
});

window.tableModes = { main: 'BUY', hedge: 'BUY' };

function getColorClass(val) {
    return val < 0 ? "neg" : "pos";
}

function getTableMode(type) {
    return window.tableModes[type] || 'BUY';
}

function toggleColumn(tableId, colIndex, checked) {
    const table = document.getElementById(tableId);
    if (!table) return;
    const rows = table.querySelectorAll("tbody tr");
    rows.forEach(function(row) {
        const cell = row.children[colIndex];
        if (cell) {
            const checkbox = cell.querySelector("input[type='checkbox']");
            if (checkbox) checkbox.checked = checked;
        }
    });
}

function resetCheckAllForSide(side, checked) {
    if (side === "main") {
        document.getElementById("main-ce-checkall").checked = checked;
        document.getElementById("main-pe-checkall").checked = checked;
    } else if (side === "hedge") {
        document.getElementById("hedge-ce-checkall").checked = checked;
        document.getElementById("hedge-pe-checkall").checked = checked;
    }
}

function renderDashboard(diffRows, hedgeRows, mainFresh, hedgeFresh) {
    var now = Math.floor(Date.now() / 1000);
    var diffHtml = "";
    var sCeLtp = 0, sPrCe = 0, sPrPe = 0, sPeLtp = 0;

    diffRows.forEach(function(row) {
        sCeLtp += row.curr_ce;
        sPrCe += row.prev_ce;
        sPrPe += row.prev_pe;
        sPeLtp += row.curr_pe;
        var leftId = "cb-main-ce-" + row.ce_strike;
        var rightId = "cb-main-pe-" + row.pe_strike;
        var exLeft = document.getElementById(leftId);
        var exRight = document.getElementById(rightId);
        var isLeftChecked = mainFresh ? true : (exLeft ? exLeft.checked : true);
        var isRightChecked = mainFresh ? true : (exRight ? exRight.checked : true);

        diffHtml += '<tr>' +
            '<td class="cb-cell"><input type="checkbox" id="' + leftId + '" ' + (isLeftChecked ? 'checked' : '') + ' onchange="updateCheckAllState(\'diffTable\', 0)"></td>' +
            '<td class="' + getColorClass(row.total_diff) + '">' + row.total_diff.toFixed(2) + '</td>' +
            '<td class="' + getColorClass(row.ce_diff_pct) + '">' + row.ce_diff_pct.toFixed(2) + '</td>' +
            '<td class="' + getColorClass(row.ce_diff) + '">' + row.ce_diff.toFixed(2) + '</td>' +
            '<td>' + row.curr_ce.toFixed(2) + '</td>' +
            '<td>' + row.prev_ce.toFixed(2) + '</td>' +
            '<td>' + row.ce_strike + '</td>' +
            '<td>' + row.pe_strike + '</td>' +
            '<td>' + row.prev_pe.toFixed(2) + '</td>' +
            '<td>' + row.curr_pe.toFixed(2) + '</td>' +
            '<td class="' + getColorClass(row.pe_diff) + '">' + row.pe_diff.toFixed(2) + '</td>' +
            '<td class="' + getColorClass(row.pe_diff_pct) + '">' + row.pe_diff_pct.toFixed(2) + '</td>' +
            '<td class="' + getColorClass(row.total_diff_pct) + '">' + row.total_diff_pct + '</td>' +
            '<td class="cb-cell"><input type="checkbox" id="' + rightId + '" ' + (isRightChecked ? 'checked' : '') + ' onchange="updateCheckAllState(\'diffTable\', 13)"></td>' +
            '</tr>';
    });

    var diffFooter = '<tr class="footer-row"><td colspan="4"></td><td>' + sCeLtp.toFixed(2) + '</td><td>' + sPrCe.toFixed(2) + '</td>' +
        '<td colspan="2" style="text-align:center; font-weight:bold;">TOTALS</td><td>' + sPrPe.toFixed(2) + '</td><td>' + sPeLtp.toFixed(2) + '</td><td colspan="4"></td></tr>';

    var mainBody = document.getElementById("mainBody");
    if (mainBody) mainBody.innerHTML = diffHtml + diffFooter;

    var hedgeHtml = "";
    hedgeRows.forEach(function(row) {
        var hLeftId = "cb-hedge-ce-" + row.ce_strike;
        var hRightId = "cb-hedge-pe-" + row.pe_strike;
        var exHLeft = document.getElementById(hLeftId);
        var exHRight = document.getElementById(hRightId);
        var isHLeftChecked = hedgeFresh ? true : (exHLeft ? exHLeft.checked : true);
        var isHRightChecked = hedgeFresh ? true : (exHRight ? exHRight.checked : true);

        hedgeHtml += '<tr>' +
            '<td class="cb-cell"><input type="checkbox" id="' + hLeftId + '" ' + (isHLeftChecked ? 'checked' : '') + ' onchange="updateCheckAllState(\'hedgeTable\', 0)"></td>' +
            '<td>' + row.curr_ce.toFixed(2) + '</td>' +
            '<td>' + row.ce_strike + '</td>' +
            '<td>' + row.pe_strike + '</td>' +
            '<td>' + row.curr_pe.toFixed(2) + '</td>' +
            '<td class="cb-cell"><input type="checkbox" id="' + hRightId + '" ' + (isHRightChecked ? 'checked' : '') + ' onchange="updateCheckAllState(\'hedgeTable\', 5)"></td>' +
            '</tr>';
    });

    var hedgeBody = document.getElementById("hedgeBody");
    if (hedgeBody) hedgeBody.innerHTML = hedgeHtml;

    if (diffRows.length > 0) {
        if (currentLine) currentLine.update({ time: now, value: sCeLtp + sPeLtp });
        if (mainLine) mainLine.update({ time: now, value: sPrCe + sPrPe });
    }
}

function updateCheckAllState(tableId, colIndex) {
    var table = document.getElementById(tableId);
    if (!table) return;
    var rows = table.querySelectorAll("tbody tr:not(.footer-row)");
    var allChecked = true;
    rows.forEach(function(row) {
        var cell = row.children[colIndex];
        if (cell) {
            var checkbox = cell.querySelector("input[type='checkbox']");
            if (checkbox && !checkbox.checked) allChecked = false;
        }
    });
    var checkallId = (tableId === "mainTable") ? 
        (colIndex === 0 ? "main-ce-checkall" : "main-pe-checkall") :
        (colIndex === 0 ? "hedge-ce-checkall" : "hedge-pe-checkall");
    var checkall = document.getElementById(checkallId);
    if (checkall) checkall.checked = allChecked;
}

async function updateSubscription(side) {
    var symbol = document.getElementById("symbol-select").value;
    var expiry = document.getElementById("expiry-select").value;
    var ce_start = document.getElementById(side + "-call-base").value;
    var pe_start = document.getElementById(side + "-put-base").value;

    if (!symbol || !expiry || !ce_start || !pe_start) {
        alert("Please select Symbol, Expiry, Call Strike, and Put Strike");
        return;
    }

    var payload = {
        side: side,
        basename: symbol,
        expiry: expiry,
        ce_start: parseInt(ce_start),
        pe_start: parseInt(pe_start),
        num_of_strikes: parseInt(document.getElementById(side + "-num").value)
    };

    try {
        var response = await fetch("/api/logic/update-subscription", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        var result = await response.json();
        if (result.status === "success") {
            resetCheckAllForSide(side, true);
        }
    } catch (error) {
        console.error("Subscription update failed:", error);
    }
}

function playBeep() {
    try {
        var ctx = new (window.AudioContext || window.webkitAudioContext)();
        var osc = ctx.createOscillator();
        osc.connect(ctx.destination);
        osc.frequency.value = 800;
        osc.start();
        osc.stop(0.1);
    } catch(e) {}
}

function showToast(message, isSuccess) {
    var toast = document.createElement("div");
    toast.className = "toast " + (isSuccess ? "success" : "error");
    toast.textContent = message;
    document.body.appendChild(toast);
    playBeep();
    setTimeout(function() { toast.remove(); }, 3000);
}

async function processBatchOrders(tableId, modeType, qtyId, orderCode) {
    document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = true; });

    var table = document.getElementById(tableId);
    if (!table) {
        showToast("Table not found!", false);
        document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = false; });
        return;
    }
    
    var checkedBoxes = table.querySelectorAll("tbody input[type='checkbox']:checked");
    var qtyElement = document.getElementById(qtyId);
    if (!qtyElement) {
        showToast("Quantity input not found!", false);
        document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = false; });
        return;
    }
    var qty = parseInt(qtyElement.value);
    
    var numStrikesElement = document.getElementById(modeType + "-num");
    if (!numStrikesElement) {
        showToast("Number of strikes input not found!", false);
        document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = false; });
        return;
    }
    var numStrikes = parseInt(numStrikesElement.value);
    
    var side = orderCode.startsWith("L") ? "BUY" : "SELL";

    if (checkedBoxes.length === 0) {
        showToast("Select at least one strike!", false);
        document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = false; });
        return;
    }

    var orderList = Array.from(checkedBoxes).map(function(cb) { return cb.id; });
    var payload = {
        orders: orderList,
        quantity: qty,
        order_code: orderCode,
        tag: modeType
    };

    try {
        var res = await fetch("/api/logic/order_place", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        var result = await res.json();
        if (result.status === "success") {
            showToast(orderList.length + " " + side + " orders sent", true);
        } else {
            showToast(result.message || "Order failed", false);
        }
    } catch (error) {
        showToast("Order request failed", false);
    } finally {
        document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = false; });
    }
}

function mainFire() { placeOrder("main", "main-qty", false); }
function mainSquare() { placeSquareOrder("main", "main-qty", true); }
function hedgeFire() { placeOrder("hedge", "hedge-qty", false); }
function hedgeSquare() { placeSquareOrder("hedge", "hedge-qty", true); }

async function placeSquareOrder(tableTag, qtyId, isSquareOff) {
    var tableId = tableTag === "main" ? "mainTable" : "hedgeTable";
    if (!document.getElementById(tableId)) {
        showToast("Table not found!", false);
        return;
    }

    var side = getTableMode(tableTag);
    var qtyElement = document.getElementById(qtyId);
    if (!qtyElement) {
        showToast("Quantity input not found!", false);
        return;
    }
    var qty = qtyElement.value;
    var table = document.getElementById(tableId);
    var checkedBoxes = table.querySelectorAll("tbody input[type='checkbox']:checked");
    if (checkedBoxes.length === 0) {
        showToast("Select at least one strike!", false);
        return;
    }

    var orderCode = (side === "BUY" ? "S" : "L") + "X";
    var tag = tableTag;

    document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = true; });

    for (var i = 0; i < checkedBoxes.length; i++) {
        var cb = checkedBoxes[i];
        var orderId = cb.id;
        try {
            var res = await fetch("/api/logic/order_place_one", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    trading_symbol: orderId,
                    quantity: parseInt(qty),
                    order_type: orderCode,
                    tag: tag
                })
            });
            var result = await res.json();
            if (result.status !== "success") {
                showToast("Order " + (i+1) + " failed", false);
            }
        } catch (error) {
            showToast("Order " + (i+1) + " request failed", false);
        }
    }

    document.querySelectorAll(".action-btn").forEach(function(b) { b.disabled = false; });
    showToast(checkedBoxes.length + (side === "BUY" ? "BUY" : "SELL") + " orders sent", true);
}

function placeOrder(tableTag, qtyId, isSquareOff) {
    var tableId = tableTag === "main" ? "mainTable" : "hedgeTable";
    if (!document.getElementById(tableId)) {
        showToast("Table not found!", false);
        return;
    }
    
    var side = getTableMode(tableTag);
    var qtyElement = document.getElementById(qtyId);
    if (!qtyElement) {
        showToast("Quantity input not found!", false);
        return;
    }
    var qty = qtyElement.value;
    
    var code = (side === "BUY" ? "S" : "L") + (isSquareOff ? "X" : "E");
    
    processBatchOrders(tableId, tableTag, qtyId, code);
}

async function showLogsModal() {
    var modal = document.getElementById("logsModal");
    var content = document.getElementById("logsContent");
    modal.style.display = "block";
    content.textContent = "Loading...";
    try {
        var resp = await fetch("/logs");
        content.textContent = await resp.text();
    } catch(e) {
        content.textContent = "Error loading logs: " + e;
    }
}

function closeLogsModal() {
    document.getElementById("logsModal").style.display = "none";
}

function showSettingsModal() {
    loadSettings();
    document.getElementById("settingsModal").style.display = "block";
}

function closeSettingsModal() {
    document.getElementById("settingsModal").style.display = "none";
}

async function loadSettings() {
    try {
        var response = await fetch("/api/logic/settings");
        var settings = await response.json();
        document.getElementById("settingsWebhook").value = settings.webhook_url || "";
        document.getElementById("settingsTag").value = settings.tag || "poweroption";
        document.getElementById("settingsTimeout").value = settings.timeout || 30;
    } catch (e) {
        console.error("Error loading settings: " + e.message);
    }
}

async function saveSettings() {
    var payload = {
        webhook_url: document.getElementById("settingsWebhook").value,
        tag: document.getElementById("settingsTag").value,
        timeout: parseInt(document.getElementById("settingsTimeout").value),
    };
    try {
        await fetch("/api/logic/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        closeSettingsModal();
        window.location.reload();
    } catch (e) {
        console.error("Error saving settings: " + e.message);
    }
}

function toggleSide(type) {
    var checkboxId = type === "main" ? "main-side-toggle" : "hedge-side-toggle";
    var checkbox = document.getElementById(checkboxId);
    if (checkbox) {
        window.tableModes[type] = checkbox.checked ? "SELL" : "BUY";
    }
}

async function restartLogic() {
    await fetch("/api/logic/stop", { method: "POST" });
    await new Promise(function(r) { setTimeout(r, 500); });
    await fetch("/api/logic/start", { method: "POST" });
    window.location.reload();
}