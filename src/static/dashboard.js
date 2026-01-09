const chartElement = document.getElementById('chart-container');

const chart = LightweightCharts.createChart(chartElement, {
  width: chartElement.offsetWidth, // This will correctly pick up the "remaining" width
  height: chartElement.offsetHeight,
  layout: {
    background: { color: '#131722' },
    textColor: '#d1d4dc',
  },
  // ... other options
});

const mainLine = chart.addSeries(LightweightCharts.LineSeries, { color: 'purple' }); // Previous Day Close
const currentLine = chart.addSeries(LightweightCharts.LineSeries, { color: 'green' }); // Current Price

const socket = new WebSocket('ws://localhost:8000/ws');

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  // Update chart and LTP values in the table
  currentLine.update({ time: data.time, value: data.ltp });
};


