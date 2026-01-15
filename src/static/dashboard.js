// Wrap in DOMContentLoaded to ensure #chart-container exists in the DOM
document.addEventListener('DOMContentLoaded', () => {
  const chartElement = document.getElementById('chart-container');

  // 1. Safety Check: If the element doesn't exist, stop here
  if (!chartElement) {
    console.error("CRITICAL: #chart-container not found in HTML. Check index.html.");
    return;
  }

  // 2. Initialize Chart
  // We use 'window.chart' to ensure it's globally accessible and not shadowed
  window.chart = LightweightCharts.createChart(chartElement, {
    width: chartElement.clientWidth,
    height: chartElement.clientHeight,
    layout: {
      backgroundColor: '#ffffff',
      textColor: '#333',
    },
    grid: {
      vertLines: { color: '#f0f3fa' },
      horzLines: { color: '#f0f3fa' },
    },
    timeScale: {
      timeVisible: true,
      secondsVisible: true,
    },
  });

  // 3. Initialize Series
  // IMPORTANT: addLineSeries is the correct method for v3.x and v4.x
  const mainLine = window.chart.addLineSeries({
    color: '#9c27b0',
    lineWidth: 2,
    title: 'Baseline (0)'
  });

  const currentLine = window.chart.addLineSeries({
    color: '#ff9800',
    lineWidth: 3,
    title: 'Total Diff'
  });

  // 4. Handle Layout Resizing
  window.addEventListener('resize', () => {
    window.chart.applyOptions({
      width: chartElement.clientWidth,
      height: chartElement.clientHeight
    });
  });

  // 5. WebSocket Logic
  const socket = new WebSocket(`ws://${window.location.host}/ws`);
  const chainBody = document.getElementById('chainBody');

  socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "UPDATE") {
      renderDashboard(data.rows, mainLine, currentLine);
    }
  };
});

function renderDashboard(rows, mainLine, currentLine) {
  let html = "";
  let totals = { ce_diff: 0, prev_ce: 0, pe_diff: 0, prev_pe: 0, total_diff: 0 };
  const now = Math.floor(Date.now() / 1000);

  rows.forEach(row => {
    html += `
            <tr>
                <td class="${getColorClass(row.total_diff)}">${row.total_diff.toFixed(2)}</td>
                <td class="${getColorClass(row.ce_diff)}">${row.ce_diff_pct}</td>
                <td class="${getColorClass(row.ce_diff)}">${row.ce_diff.toFixed(2)}</td>
                <td>${row.curr_ce.toFixed(2)}</td>
                <td>${row.prev_ce.toFixed(2)}</td>
                <td style="background:#f1f3f5; font-weight:bold;">${row.ce_strike}</td>
                <td style="background:#f1f3f5; font-weight:bold;">${row.pe_strike}</td>
                <td>${row.prev_pe.toFixed(2)}</td>
                <td>${row.curr_pe.toFixed(2)}</td>
                <td class="${getColorClass(row.pe_diff)}">${row.pe_diff.toFixed(2)}</td>
                <td class="${getColorClass(row.pe_diff)}">${row.pe_diff_pct}</td>
                <td class="${getColorClass(row.total_diff)}">${((row.total_diff / (row.prev_ce + row.prev_pe)) * 100).toFixed(2)}%</td>
            </tr>
        `;
    totals.ce_diff += row.ce_diff;
    totals.prev_ce += row.prev_ce;
    totals.pe_diff += row.pe_diff;
    totals.prev_pe += row.prev_pe;
    totals.total_diff += row.total_diff;
  });

  document.getElementById('chainBody').innerHTML = html;

  // UPDATE THE CHART LINES
  // currentLine.update will now work because it's passed from the initialized scope
  currentLine.update({ time: now, value: totals.total_diff });
  mainLine.update({ time: now, value: 0 });
}

function getColorClass(val) { return val < 0 ? "neg" : "pos"; }


function updateStrikes() {
  const symbol = document.getElementById('symbol-select').value;
  const base = document.getElementById('base-strike').value;
  const count = document.getElementById('num-strikes').value;

  console.log(`Requesting ${count} strikes for ${symbol} starting at ${base}`);

  // Send the configuration to the backend via the existing WebSocket
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({
      action: "SUBSCRIBE",
      symbol: symbol,
      base_strike: parseInt(base),
      num_strikes: parseInt(count)
    }));
  }
}

// Ensure the integer-only constraint for "No. of Strikes"
document.getElementById('num-strikes').addEventListener('input', function() {
  this.value = this.value.replace(/[^0-9]/g, '');
});
