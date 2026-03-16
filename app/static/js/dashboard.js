/*
Mini README:
Client-side dashboard helper script.
- Renders the live sensor chart.
- Powers a simple OPEN/CLOSED door widget for on/off style sensors.
- Emits console debug logs so each behavior is easy to audit.
*/

async function loadSensorChart() {
  const canvas = document.getElementById('sensorChart');
  if (!canvas || typeof Chart === 'undefined') return;

  try {
    const response = await fetch('/api/sensor/latest');
    if (!response.ok) {
      console.warn('Chart refresh failed with status:', response.status);
      return;
    }

    const data = await response.json();
    const labels = data.map((d) => new Date(d.created_at).toLocaleTimeString());
    const values = data.map((d) => d.value);

    if (window.sensorChartInstance) {
      window.sensorChartInstance.destroy();
    }

    window.sensorChartInstance = new Chart(canvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{ label: 'Sensor', data: values, borderColor: '#00d4ff' }]
      },
      options: { responsive: true }
    });
  } catch (error) {
    console.error('Chart refresh failed due to network or parsing error:', error);
  }
}

function readDoorTopic() {
  const topicInput = document.getElementById('doorTopic');
  if (!topicInput) return '';

  const savedTopic = localStorage.getItem('iotdash-door-topic');
  if (savedTopic && !topicInput.dataset.hydrated) {
    topicInput.value = savedTopic;
    topicInput.dataset.hydrated = 'true';
  }

  const topic = topicInput.value.trim();
  localStorage.setItem('iotdash-door-topic', topic);
  return topic;
}

function renderDoorWidget(payload) {
  const widget = document.getElementById('doorStatusWidget');
  const value = document.getElementById('doorStatusValue');
  const meta = document.getElementById('doorStatusMeta');
  if (!widget || !value || !meta) return;

  widget.classList.remove('door-open', 'door-closed', 'door-unknown');
  const state = payload.state || 'UNKNOWN';
  value.textContent = state;

  if (state === 'OPEN') {
    widget.classList.add('door-open');
  } else if (state === 'CLOSED') {
    widget.classList.add('door-closed');
  } else {
    widget.classList.add('door-unknown');
  }

  if (payload.created_at) {
    const timestamp = new Date(payload.created_at).toLocaleString();
    meta.textContent = `Topic: ${payload.topic} | Last update: ${timestamp} | Raw value: ${payload.value}`;
  } else {
    meta.textContent = `Topic: ${payload.topic} | No data yet.`;
  }
}

async function refreshDoorWidget() {
  const widget = document.getElementById('doorStatusWidget');
  if (!widget) return;

  const topic = readDoorTopic();
  if (!topic) {
    renderDoorWidget({ topic: '(empty)', state: 'UNKNOWN' });
    return;
  }

  try {
    const response = await fetch(`/api/sensor/door-status?topic=${encodeURIComponent(topic)}`);
    if (!response.ok) {
      console.warn('Door widget refresh failed with status:', response.status);
      return;
    }
    const payload = await response.json();
    console.debug('Door widget refreshed:', payload);
    renderDoorWidget(payload);
  } catch (error) {
    console.error('Door widget refresh failed:', error);
  }
}

function bindDoorTopicInput() {
  const topicInput = document.getElementById('doorTopic');
  if (!topicInput) return;

  topicInput.addEventListener('change', refreshDoorWidget);
  topicInput.addEventListener('keyup', (event) => {
    if (event.key === 'Enter') refreshDoorWidget();
  });
}

loadSensorChart();
setInterval(loadSensorChart, 10000);
bindDoorTopicInput();
refreshDoorWidget();
setInterval(refreshDoorWidget, 5000);


async function refreshMqttStatus() {
  const statusEl = document.getElementById('mqttStatusText');
  if (!statusEl) return;

  try {
    const response = await fetch('/api/mqtt/status');
    if (!response.ok) {
      statusEl.textContent = 'Live status: unable to fetch MQTT status.';
      return;
    }
    const status = await response.json();
    const topics = Object.keys(status.subscribed_topics || {});
    statusEl.textContent = status.connected
      ? `Live status: CONNECTED to ${status.host}:${status.port} | Subscriptions: ${topics.length}`
      : `Live status: DISCONNECTED${status.last_error ? ` | ${status.last_error}` : ''}`;
  } catch (error) {
    statusEl.textContent = 'Live status: MQTT status request failed.';
    console.error('MQTT status refresh failed:', error);
  }
}

refreshMqttStatus();
setInterval(refreshMqttStatus, 5000);
