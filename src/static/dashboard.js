/**
 * Dashboard.js
 * Optimized for dual-table rendering (14-column Diff vs 6-column Hedge)
 */

let chart;
let mainLine;
let currentLine;
let socket;

document.addEventListener("DOMContentLoaded", () => {
    // Initialize toggles to unchecked (buy mode)
    document.getElementById("main-side-toggle").checked = false;
    document.getElementById("hedge-side-toggle").checked = false;
    
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
            return new Date(timestamp * 1000).toLocaleTimeString("en-IN", {
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
                hour: '2-digit',
                minute: '2-digit',
                hour12: false
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
        const leftId = `cb-diff-ce-${row.ce_strike}`;
        const rightId = `cb-diff-pe-${row.pe_strike}`;
        
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

    const diffBody = document.getElementById("diffBody");
    if (diffBody) diffBody.innerHTML = diffHtml + diffFooter;

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
 * Collects checked strikes by parsing existing element IDs
 */
async function processBatchOrders(tableId, modeType, qtyId, isSquareOff = false) {
    const table = document.getElementById(tableId);
    const checkedBoxes = table.querySelectorAll('tbody input[type="checkbox"]:checked');
    const lots = document.getElementById(qtyId).value;
    
    let side = getTableMode(modeType); // From toggle.js
    if (isSquareOff) side = (side === 'BUY') ? 'SELL' : 'BUY';

    if (checkedBoxes.length === 0) {
        alert("Please select at least one strike!");
        return;
    }

    // Parse IDs like "cb-diff-ce-22000"
    const orderList = Array.from(checkedBoxes).map(cb => {
        const parts = cb.id.split('-'); 
        return {
            type: parts[2].toUpperCase(), // "ce" -> "CE"
            strike: parseInt(parts[3])    // "22000" -> 22000
        };
    });

    const payload = {
        orders: orderList,
        quantity: parseInt(lots),
        transaction_type: side,
        tag: modeType
    };

    try {
        await fetch('/order_place', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        console.log(`Sent ${orderList.length} ${side} orders for ${modeType}`);
    } catch (error) {
        console.error("Order request failed:", error);
    }
}


// Button Mappings
function diffFire()   { processBatchOrders('diffTable', 'diff', 'main-qty', false); }
function diffSquare() { processBatchOrders('diffTable', 'diff', 'main-qty', true); }
function hedgeFire()  { processBatchOrders('hedgeTable', 'hedge', 'hedge-qty', false); }
function hedgeSquare(){ processBatchOrders('hedgeTable', 'hedge', 'hedge-qty', true); }


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
    const rows = table.querySelectorAll("tbody tr");
    rows.forEach(row => {
        const cell = row.children[colIndex];
        const checkbox = cell.querySelector("input[type='checkbox']");
        if (checkbox) checkbox.checked = checked;
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
        ? (colIndex === 0 ? "diff-ce-checkall" : "diff-pe-checkall")
        : (colIndex === 0 ? "hedge-ce-checkall" : "hedge-pe-checkall");
    const checkall = document.getElementById(checkallId);
    if (checkall) checkall.checked = allChecked;
}

function resetCheckAllBoxes() {
    document.getElementById("diff-ce-checkall").checked = false;
    document.getElementById("diff-pe-checkall").checked = false;
    document.getElementById("hedge-ce-checkall").checked = false;
    document.getElementById("hedge-pe-checkall").checked = false;
}

function resetCheckAllForSide(side, checked = false) {
    if (side === "main") {
        document.getElementById("diff-ce-checkall").checked = checked;
        document.getElementById("diff-pe-checkall").checked = checked;
    } else if (side === "hedge") {
        document.getElementById("hedge-ce-checkall").checked = checked;
        document.getElementById("hedge-pe-checkall").checked = checked;
    }
}
