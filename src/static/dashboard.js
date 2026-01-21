/**
 * Dashboard.js
 * Frontend-only calculations for totals in the sticky last row.
 */

let chart;
let mainLine;
let currentLine;
let socket;
let currentSide = 'BUY'; // Default to Buy

document.addEventListener('DOMContentLoaded', () => {
  const chartElement = document.getElementById('chart-container');
  if (chartElement) {
    chart = LightweightCharts.createChart(chartElement, {
      width: chartElement.clientWidth,
      height: chartElement.clientHeight,
      layout: { background: { color: '#131722' }, textColor: '#d1d4dc' },
      grid: { vertLines: { color: '#1e222d' }, horzLines: { color: '#1e222d' } },
      timeScale: { timeVisible: true, secondsVisible: true },
    });

    mainLine = chart.addLineSeries({ color: '#9c27b0', title: 'Baseline' });
    currentLine = chart.addLineSeries({ color: '#ff9800', title: 'Total Diff' });

    window.addEventListener('resize', () => {
      chart.applyOptions({ width: chartElement.clientWidth, height: chartElement.clientHeight });
    });
  }

  socket = new WebSocket(`ws://${window.location.host}/ws`);
  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "UPDATE") {
      renderDashboard(data.rows);
    }
  };
});

function renderDashboard(rows) {
  let html = "";
  const now = Math.floor(Date.now() / 1000);

  // 1. Initialize Total Accumulators
  let sumCeLtp = 0;
  let sumPrevCe = 0;
  let sumPrevPe = 0;
  let sumPeLtp = 0;
  let totalLiveLtp = 0
  let totalStaticPrev = 0


  rows.forEach(row => {
    // 2. Accumulate Values
    sumCeLtp += row.curr_ce;
    sumPrevCe += row.prev_ce;
    sumPrevPe += row.prev_pe;
    sumPeLtp += row.curr_pe;


    // 3. Generate Data Rows
    html += `
            <tr>
                <td class="cb-cell"><input type="checkbox" class="ce-check"></td>
                <td class="${getColorClass(row.total_diff)}">${row.total_diff.toFixed(2)}</td>
                <td class="${getColorClass(row.ce_diff)}">${row.ce_diff_pct}</td>
                <td class="${getColorClass(row.ce_diff)}">${row.ce_diff.toFixed(2)}</td>
                <td>${row.curr_ce.toFixed(2)}</td>
                <td>${row.prev_ce.toFixed(2)}</td>
                <td class="strike-cell">${row.ce_strike}</td>
                <td class="strike-cell">${row.pe_strike}</td>
                <td>${row.prev_pe.toFixed(2)}</td>
                <td>${row.curr_pe.toFixed(2)}</td>
                <td class="${getColorClass(row.pe_diff)}">${row.pe_diff.toFixed(2)}</td>
                <td class="${getColorClass(row.pe_diff)}">${row.pe_diff_pct}</td>
                <td class="${getColorClass(row.total_diff)}">${row.total_diff_pct}</td>
                <td class="cb-cell"><input type="checkbox" class="pe-check"></td>
            </tr>`;
  });

  // 4. Generate the "Sticky" Totals Row
  // Column counts must match the header (14 cols total). 
  // Using colspan="2" on the strike cell to merge them.
  html += `
        <tr class="footer-row">
            <td class="cb-cell"></td> <td></td>                 <td></td>                 <td></td>                 <td>${sumCeLtp.toFixed(2)}</td>
            <td>${sumPrevCe.toFixed(2)}</td>
            <td colspan="2" class="strike-cell" style="text-align: center;">TOTALS</td>
            <td>${sumPrevPe.toFixed(2)}</td>
            <td>${sumPeLtp.toFixed(2)}</td>
            <td></td>                 <td></td>                 <td></td>                 <td class="cb-cell"></td> </tr>`;

  totalLiveLtp = sumPeLtp + sumCeLtp;
  totalStaticPrev = sumPrevPe + sumPrevCe;
  // Update table bodies
  const diffBody = document.getElementById('diffBody');
  const ltpBody = document.getElementById('ltpBody');
  if (diffBody) diffBody.innerHTML = html;
  if (ltpBody) ltpBody.innerHTML = html;

  // Update Chart
  if (currentLine) currentLine.update({ time: now, value: totalLiveLtp });
  if (mainLine) mainLine.update({ time: now, value: totalStaticPrev });
}

function getColorClass(val) { return val < 0 ? "neg" : "pos"; }

function updateStrikes() {
  const symbol = document.getElementById('symbol-select').value;
  const base = document.getElementById('base-strike').value;
  const count = document.getElementById('num-strikes').value;
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      action: "SUBSCRIBE", symbol, base_strike: parseInt(base), num_strikes: parseInt(count)
    }));
  }
}

function fireOrders() { console.log("Fire button clicked"); }
function fireHedge() { console.log("Hedge button clicked"); }


function toggleSide() {
  const btn = document.getElementById('side-toggle');
  const container = document.querySelector('.dashboard-container');

  if (currentSide === 'BUY') {
    currentSide = 'SELL';
    btn.textContent = 'SELL';
    btn.classList.remove('buy-mode');
    btn.classList.add('sell-mode');
    container.classList.remove('buy-mode-active');
    container.classList.add('sell-mode-active');
  } else {
    currentSide = 'BUY';
    btn.textContent = 'BUY';
    btn.classList.remove('sell-mode');
    btn.classList.add('buy-mode');
    container.classList.remove('sell-mode-active');
    container.classList.add('buy-mode-active');
  }
}


