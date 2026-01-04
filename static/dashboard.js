const chart = LightweightCharts.createChart(document.getElementById('chart-container'), {
  width: 800, height: 400,
  layout: { backgroundColor: '#ffffff', textColor: '#000000' }
});

const mainLine = chart.addSeries(LightweightCharts.LineSeries, { color: 'purple' }); // Previous Day Close
const currentLine = chart.addSeries(LightweightCharts.LineSeries, { color: 'green' }); // Current Price

const socket = new WebSocket('ws://localhost:8000/ws');

socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  // Update chart and LTP values in the table
  currentLine.update({ time: data.time, value: data.ltp });
};

