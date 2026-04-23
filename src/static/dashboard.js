/**
 * Dashboard.js
 * Optimized for dual-table rendering (14-column Diff vs 6-column Hedge)
 */

let chart;
let mainLine;
let currentLine;
let socket;

// Initialize chart and socket
    const chartElement = document.getElementById("chart-container");
    if (chartElement) {
    
    // Sync initial state from toggles
    const mainToggle = document.getElementById("main-side-toggle");
    const hedgeToggle = document.getElementById("hedge-side-toggle");
    if (mainToggle) tableModes.main = mainToggle.checked ? 'SELL' : 'BUY';
    if (hedgeToggle) tableModes.hedge = hedgeToggle.checked ? 'SELL' : 'BUY';
    console.log(`Initial modes: main=${tableModes.main}, hedge=${tableModes.hedge}`);
    
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
    localization: {
        // This formats the price/time in the floating tooltip
timeFormatter: timestamp => {
            const d = new Date(timestamp * 1000);
            return d.toLocaleTimeString("en-IN", {
                timeZone: "Asia/Kolkata",
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },
    },
    timeScale: { 
        timeVisible: true, 
        secondsVisible: true,
        shiftVisibleRangeOnNewBar: true,

// This forces the axis labels to use your local time
        tickMarkFormatter: (time, tickMarkType, locale) => {
            const date = new Date(time * 1000);
            return date.toLocaleTimeString("en-IN", {
                timeZone: "Asia/Kolkata",
                hour12: false,
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        },
    },
        });

        mainLine = chart.addLineSeries({ color: "#9c27b0", title: "Baseline" });
        currentLine = chart.addLineSeries({
            color: "#ff9800",
            title: "Total Diff",
        });
    }

socket = new WebSocket(`ws://${window.location.host}/ws`);
    socket.onopen = () => {
        updateConnectionStatus(true);
    };
    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === "UPDATE") {
            renderDashboard(data.diff_rows || [], data.hedge_rows || [], data.main_fresh || 0, data.hedge_fresh || 0);
        }
    };
    socket.onclose = () => {
        console.log("WebSocket closed");
        updateConnectionStatus(false);
    };

    // Resizable chart section
    const resizeHandle = document.getElementById("resize-handle");
    const chartSection = document.getElementById("chart-section");
    const tablesWrapper = document.getElementById("tables-wrapper");
    const dashboardContainer = document.querySelector(".dashboard-container");
    
    if (resizeHandle && chartSection && tablesWrapper) {
        let isResizing = false;
        let startY = 0;
        let startChartHeight = 0;
        
        resizeHandle.addEventListener("mousedown", (e) => {
            isResizing = true;
            startY = e.clientY;
            startChartHeight = chartSection.offsetHeight;
            document.body.style.cursor = "ns-resize";
            document.body.style.userSelect = "none";
        });
        
        document.addEventListener("mousemove", (e) => {
            if (!isResizing) return;
            
            const deltaY = startY - e.clientY;  // Flip direction
            const containerHeight = dashboardContainer.offsetHeight;
            let newChartHeight = startChartHeight + deltaY;
            
            // Constrain between 10% and 80%
            newChartHeight = Math.max(containerHeight * 0.1, Math.min(containerHeight * 0.8, newChartHeight));
            
            chartSection.style.height = newChartHeight + "px";
            if (chart) {
                chart.resize(chartSection.offsetWidth, chartSection.offsetHeight - 8);
            }
        });
        
        document.addEventListener("mouseup", () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.cursor = "";
                document.body.style.userSelect = "";
            }
        });
    }
    
    // Window resize handler
    window.addEventListener("resize", () => {
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

window.addEventListener("beforeunload", () => {
    if (socket) {
        socket.close();
    }
});


/**
 * Fully Optimized renderDashboard
 * Independently tracks Call and Put checkboxes for both Diff and Hedge tables.
 */
function renderDashboard(diffRows, hedgeRows, mainFresh, hedgeFresh) {
    const now = Math.floor(Date.now() / 1000);

    // --- 1. Render DIFF TABLE (14 Columns) ---
    let diffHtml = "";
    let sCeLtp = 0, sPrCe = 0, sPrPe = 0, sPeLtp = 0;

    diffRows.forEach((row) => {
        sCeLtp += row.curr_ce;
        sPrCe += row.prev_ce;
        sPrPe += row.prev_pe;
        sPeLtp += row.curr_pe;

        // Unique IDs for Left (Call) and Right (Put)
        const leftId = `cb-main-ce-${row.ce_strike}`;
        const rightId = `cb-main-pe-${row.pe_strike}`;
        
        // Lookup existing state
        const exLeft = document.getElementById(leftId);
        const exRight = document.getElementById(rightId);

        // State logic: Fresh flag > Existing DOM state > Default true
        const isLeftChecked = mainFresh ? true : (exLeft ? exLeft.checked : true);
        const isRightChecked = mainFresh ? true : (exRight ? exRight.checked : true);

diffHtml += `
      <tr>
        <td class="cb-cell"><input type="checkbox" id="${leftId}" ${isLeftChecked ? 'checked' : ''} onchange="updateCheckAllState('diffTable', 0)"></td>
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
        <td class="cb-cell"><input type="checkbox" id="${rightId}" ${isRightChecked ? 'checked' : ''} onchange="updateCheckAllState('diffTable', 13)"></td>
      </tr>`;
    });

    const diffFooter = `
    <tr class="footer-row">
      <td colspan="4"></td>
      <td>${sCeLtp.toFixed(2)}</td><td>${sPrCe.toFixed(2)}</td>
      <td colspan="2" style="text-align:center; font-weight:bold;">TOTALS</td>
      <td>${sPrPe.toFixed(2)}</td><td>${sPeLtp.toFixed(2)}</td>
      <td colspan="4"></td>
    </tr>`;

const mainBody = document.getElementById("mainBody");
    if (mainBody) mainBody.innerHTML = diffHtml + diffFooter;

    // --- 2. Render HEDGE TABLE (6 Columns) ---
    let hedgeHtml = "";
    hedgeRows.forEach((row) => {
        // Unique IDs for Hedge Left (Call) and Right (Put)
        const hLeftId = `cb-hedge-ce-${row.ce_strike}`;
        const hRightId = `cb-hedge-pe-${row.pe_strike}`;

        const exHLeft = document.getElementById(hLeftId);
        const exHRight = document.getElementById(hRightId);

        const isHLeftChecked = hedgeFresh ? true : (exHLeft ? exHLeft.checked : true);
        const isHRightChecked = hedgeFresh ? true : (exHRight ? exHRight.checked : true);

        hedgeHtml += `
      <tr>
<td class="cb-cell"><input type="checkbox" id="${hLeftId}" ${isHLeftChecked ? 'checked' : ''} onchange="updateCheckAllState('hedgeTable', 0)"></td>
        <td>${row.curr_ce.toFixed(2)}</td>
        <td>${row.ce_strike}</td>
        <td>${row.pe_strike}</td>
        <td>${row.curr_pe.toFixed(2)}</td>
        <td class="cb-cell"><input type="checkbox" id="${hRightId}" ${isHRightChecked ? 'checked' : ''} onchange="updateCheckAllState('hedgeTable', 5)"></td>
      </tr>`;
    });

    const hedgeBody = document.getElementById("hedgeBody");
    if (hedgeBody) hedgeBody.innerHTML = hedgeHtml;

    // --- 3. Update Chart ---
    if (diffRows.length > 0) {
        if (currentLine) currentLine.update({ time: now, value: sCeLtp + sPeLtp });
        if (mainLine) mainLine.update({ time: now, value: sPrCe + sPrPe });
    }
}


function getColorClass(val) {
    return val < 0 ? "neg" : "pos";
}

/**
 * Unified subscription updater
 * @param {string} side - Must be 'main' or 'hedge' to match HTML IDs
 */
async function updateSubscription(side) {
    // Validate all required fields are selected
    const symbol = document.getElementById("symbol-select").value;
    const expiry = document.getElementById("expiry-select").value;
    const ce_start = document.getElementById(`${side}-call-base`).value;
    const pe_start = document.getElementById(`${side}-put-base`).value;

    if (!symbol || !expiry || !ce_start || !pe_start) {
        alert("Please select Symbol, Expiry, Call Strike, and Put Strike");
        return;
    }

    // Collecting values manually using the side as the ID prefix
    const payload = {
        side: side,
        basename: symbol,
        expiry: expiry,
        ce_start: ce_start,
        pe_start: pe_start,
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
            resetCheckAllForSide(side, true);
        }
    } catch (error) {
        console.error("Subscription update failed:", error);
    }
}

/**
 * Play beep sound
 */
function playBeep() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        osc.connect(ctx.destination);
        osc.frequency.value = 800;
        osc.start();
        osc.stop(0.1);
    } catch(e) {}
}

/**
 * Show toast notification
 */
function showToast(message, isSuccess = true) {
    const toast = document.createElement('div');
    toast.className = `toast ${isSuccess ? 'success' : 'error'}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    playBeep();
    setTimeout(() => toast.remove(), 3000);
}

/**
 * Collects checked strikes by parsing existing element IDs
 */
async function processBatchOrders(tableId, modeType, qtyId, orderCode) {
    // Disable action buttons during processing
    document.querySelectorAll('.action-btn').forEach(b => b.disabled = true);

    const table = document.getElementById(tableId);
    if (!table) {
        showToast("Table not found!", false);
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
        return;
    }
    
    const checkedBoxes = table.querySelectorAll('tbody input[type="checkbox"]:checked');
    const qtyElement = document.getElementById(qtyId);
    if (!qtyElement) {
        showToast("Quantity input not found!", false);
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
        return;
    }
    const qty = qtyElement.value;
    
    // Determine the num input ID based on modeType
    let numId;
    if (modeType === 'main') {
        numId = 'main-num';
    } else if (modeType === 'hedge') {
        numId = 'hedge-num';
    } else {
        showToast("Invalid table type!", false);
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
        return;
    }
    const numStrikesElement = document.getElementById(numId);
    if (!numStrikesElement) {
        showToast("Number of strikes input not found!", false);
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
        return;
    }
    const numStrikes = numStrikesElement.value;
    
    // Derive side from orderCode first letter
    const side = orderCode.startsWith('L') ? 'BUY' : 'SELL';
    
    if (checkedBoxes.length === 0) {
        showToast("Select at least one strike!", false);
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
        return;
    }
    
    if (parseInt(qty) < 1 || parseInt(numStrikes) < 1) {
        showToast("Qty and strikes must be at least 1!", false);
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
        return;
    }

    // Simple list of selected checkbox IDs: ["cb-main-ce-22000", "cb-main-pe-23500"]
    const orderList = Array.from(checkedBoxes).map(cb => cb.id);

    const payload = {
        orders: orderList,
        quantity: parseInt(qty),
        order_code: orderCode,
        tag: modeType
    };

try {
        const res = await fetch('/order_place', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const result = await res.json();
        if (result.status === 'success') {
            showToast(`${orderList.length} ${side} orders sent`, true);
        } else {
            showToast(result.message || 'Order failed', false);
        }
    } catch (error) {
        showToast('Order request failed', false);
        console.error("Order request failed:", error);
    } finally {
        // Re-enable buttons
        document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
    }
}


// Button Mappings - simplified
function mainFire()   { placeOrder('main', 'main-qty', false); }
function mainSquare() { placeSquareOrder('main', 'main-qty', true); }
function hedgeFire()  { placeOrder('hedge', 'hedge-qty', false); }
function hedgeSquare(){ placeSquareOrder('hedge', 'hedge-qty', true); }

async function placeSquareOrder(tableTag, qtyId, isSquareOff) {
    const tableId = tableTag === 'main' ? 'mainTable' : 'hedgeTable';
    if (!document.getElementById(tableId)) {
        showToast("Table not found!", false);
        return;
    }

    const side = getTableMode(tableTag);
    const qtyElement = document.getElementById(qtyId);
    if (!qtyElement) {
        showToast("Quantity input not found!", false);
        return;
    }
    const qty = qtyElement.value;

    const table = document.getElementById(tableId);
    const checkedBoxes = table.querySelectorAll('tbody input[type="checkbox"]:checked');
    if (checkedBoxes.length === 0) {
        showToast("Select at least one strike!", false);
        return;
    }

    const orderCode = (side === 'BUY' ? 'S' : 'L') + 'X';
    const numStrikesElement = document.getElementById(tableTag === 'main' ? 'main-num' : 'hedge-num');
    const numStrikes = numStrikesElement ? numStrikesElement.value : 1;

    const tag = tableTag;

    document.querySelectorAll('.action-btn').forEach(b => b.disabled = true);

    for (let i = 0; i < checkedBoxes.length; i++) {
        const cb = checkedBoxes[i];
        const orderId = cb.id;

        try {
            const res = await fetch('/order_place_one', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    trading_symbol: orderId,
                    quantity: parseInt(qty),
                    order_type: orderCode,
                    tag: tag
                })
            });
            const result = await res.json();
            if (result.status !== 'success') {
                showToast(`Order ${i+1} failed: ${result.message || 'error'}`, false);
            }
        } catch (error) {
            showToast(`Order ${i+1} request failed`, false);
            console.error("Order request failed:", error);
        }

        }

    document.querySelectorAll('.action-btn').forEach(b => b.disabled = false);
    showToast(`${checkedBoxes.length} ${side === 'BUY' ? 'BUY' : 'SELL'} orders sent (one-by-one)`, true);
}

// Unified order function
function placeOrder(tableTag, qtyId, isSquareOff) {
    const tableId = tableTag === 'main' ? 'mainTable' : 'hedgeTable';
    if (!document.getElementById(tableId)) {
        showToast("Table not found!", false);
        return;
    }
    
    const side = getTableMode(tableTag);
    const qtyElement = document.getElementById(qtyId);
    if (!qtyElement) {
        showToast("Quantity input not found!", false);
        return;
    }
    const qty = qtyElement.value;
    
    // Order code: L/S + E/X
    // BUY toggle -> L (LE/LX), SELL toggle -> S (SE/SX)
    // Invert: BUY -> S, SELL -> L
    let code = (side === 'BUY' ? 'S' : 'L') + (isSquareOff ? 'X' : 'E');
    console.log(`placeOrder: tableTag=${tableTag}, side=${side}, isSquareOff=${isSquareOff}, code=${code}`);
    
    processBatchOrders(tableId, tableTag, qtyId, code);
}


async function showLogsModal() {
    const modal = document.getElementById("logsModal");
    const content = document.getElementById("logsContent");
    modal.style.display = "block";
    content.textContent = "Loading...";
    try {
        const resp = await fetch("/logs");
        content.textContent = await resp.text();
    } catch(e) {
        content.textContent = "Error loading logs: " + e;
    }
}

function closeLogsModal() {
    document.getElementById("logsModal").style.display = "none";
}

function toggleColumn(tableId, colIndex, checked) {
    const table = document.getElementById(tableId);
    if (!table) return;
    
    const rows = table.querySelectorAll("tbody tr");
    rows.forEach(row => {
        // Check if the row has enough columns
        if (row.children.length > colIndex) {
            const cell = row.children[colIndex];
            const checkbox = cell.querySelector("input[type='checkbox']");
            if (checkbox) checkbox.checked = checked;
        }
    });
    updateCheckAllState(tableId, colIndex);
}

function updateCheckAllState(tableId, colIndex) {
    const table = document.getElementById(tableId);
    const rows = table.querySelectorAll("tbody tr:not(.footer-row)");
    let allChecked = true;
    rows.forEach(row => {
        const cell = row.children[colIndex];
        const checkbox = cell.querySelector("input[type='checkbox']");
        if (checkbox && !checkbox.checked) {
            allChecked = false;
        }
    });
    
    const checkallId = tableId === "diffTable" 
        ? (colIndex === 0 ? "main-ce-checkall" : "main-pe-checkall")
        : (colIndex === 0 ? "hedge-ce-checkall" : "hedge-pe-checkall");
    const checkall = document.getElementById(checkallId);
    if (checkall) checkall.checked = allChecked;
}

function resetCheckAllBoxes() {
    document.getElementById("main-ce-checkall").checked = false;
    document.getElementById("main-pe-checkall").checked = false;
    document.getElementById("hedge-ce-checkall").checked = false;
    document.getElementById("hedge-pe-checkall").checked = false;
}

function resetCheckAllForSide(side, checked = false) {
    if (side === "main") {
        document.getElementById("main-ce-checkall").checked = checked;
        document.getElementById("main-pe-checkall").checked = checked;
    } else if (side === "hedge") {
        document.getElementById("hedge-ce-checkall").checked = checked;
        document.getElementById("hedge-pe-checkall").checked = checked;
    }
}

// Settings Modal Functions
function showSettingsModal() {
    loadSettings();
    document.getElementById("settingsModal").style.display = "block";
}

function closeSettingsModal() {
    document.getElementById("settingsModal").style.display = "none";
}

async function loadSettings() {
    try {
        const response = await fetch("/settings");
        const settings = await response.json();
        
        document.getElementById("settingsWebhook").value = settings.webhook_url || "";
        document.getElementById("settingsTag").value = settings.tag || "poweroption";
        document.getElementById("settingsTimeout").value = settings.timeout || 30;
        
        if (settings.log) {
            document.getElementById("settingsLogLevel").value = settings.log.level || 20;
            document.getElementById("settingsLogShow").checked = settings.log.show !== false;
        } else {
            document.getElementById("settingsLogLevel").value = 20;
            document.getElementById("settingsLogShow").checked = true;
        }
        
        showToast("Settings loaded", true);
    } catch (e) {
        showToast("Error loading settings: " + e.message, false);
    }
}

async function saveSettings() {
    const payload = {
        webhook_url: document.getElementById("settingsWebhook").value,
        tag: document.getElementById("settingsTag").value,
        timeout: parseInt(document.getElementById("settingsTimeout").value),
        log_level: parseInt(document.getElementById("settingsLogLevel").value),
        log_show: document.getElementById("settingsLogShow").checked,
    };
    
    try {
        const response = await fetch("/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        const result = await response.json();
        
        if (result.status === "success") {
            showToast("Settings saved. Session restarted.", true);
            closeSettingsModal();
        } else {
            showToast("Error: " + result.message, false);
        }
    } catch (e) {
        showToast("Error saving settings: " + e.message, false);
    }
}
