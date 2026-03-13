/*
Mini README:
Client-side dashboard helper script. Fetches latest sensor values and renders chart previews.
*/
async function loadSensorChart() {
  const canvas = document.getElementById('sensorChart');
  if (!canvas) return;
  const response = await fetch('/api/sensor/latest');
  if (!response.ok) return;
  const data = await response.json();
  const labels = data.map((d) => new Date(d.created_at).toLocaleTimeString());
  const values = data.map((d) => d.value);
  new Chart(canvas, {
    type: 'line',
    data: { labels, datasets: [{ label: 'Sensor', data: values, borderColor: '#00d4ff' }] },
    options: { responsive: true }
  });
}
loadSensorChart();
setInterval(loadSensorChart, 10000);
