const API_BASE = 'http://localhost:8000/api';
let capacityChart, voltageTempChart;

// ===========================
// 🌐 Инициализация страницы
// ===========================
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadBatteryData();
    setInterval(loadBatteryData, 30000); // Обновление каждые 30 секунд
    setupHelpTooltip();
});

// ===========================
// 📊 Инициализация графиков
// ===========================
function initializeCharts() {
    const capacityCtx = document.getElementById('capacity-chart').getContext('2d');
    const voltageTempCtx = document.getElementById('voltage-temp-chart').getContext('2d');

    capacityChart = new Chart(capacityCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Capacity (Ah)',
                data: [],
                borderColor: '#e74c3c',
                backgroundColor: 'rgba(231, 76, 60, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: { display: true, text: 'Capacity Degradation Over Time' }
            },
            scales: {
                x: { title: { display: true, text: 'Cycle Number' } },
                y: { title: { display: true, text: 'Capacity (Ah)' } }
            }
        }
    });

    voltageTempChart = new Chart(voltageTempCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Voltage (V)',
                    data: [],
                    borderColor: '#3498db',
                    backgroundColor: 'rgba(52, 152, 219, 0.1)',
                    yAxisID: 'y'
                },
                {
                    label: 'Temperature (°C)',
                    data: [],
                    borderColor: '#f39c12',
                    backgroundColor: 'rgba(243, 156, 18, 0.1)',
                    yAxisID: 'y1'
                }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                title: { display: true, text: 'Voltage and Temperature Over Time' }
            },
            scales: {
                x: { title: { display: true, text: 'Cycle Number' } },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: { display: true, text: 'Voltage (V)' }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    title: { display: true, text: 'Temperature (°C)' },
                    grid: { drawOnChartArea: false }
                }
            }
        }
    });
}

// ===========================
// 🔋 Загрузка данных батареи
// ===========================
async function loadBatteryData() {
    try {
        const batteryId = 'BATT001';
        const historyResponse = await fetch(`${API_BASE}/battery-history/${batteryId}`);
        const historyData = await historyResponse.json();

        if (historyData.data && historyData.data.length > 0) {
            updateCharts(historyData.data);
            updateCurrentStatus(historyData.data[historyData.data.length - 1]);
        }

        await predictRUL();

    } catch (error) {
        console.error('Error loading battery data:', error);
        document.getElementById('current-status').textContent = 'Error loading data';
    }
}

// ===========================
// 📈 Обновление графиков
// ===========================
function updateCharts(data) {
    const cycles = data.map(d => d.cycle_number);
    const capacities = data.map(d => d.capacity);
    const voltages = data.map(d => d.voltage);
    const temperatures = data.map(d => d.temperature);

    capacityChart.data.labels = cycles;
    capacityChart.data.datasets[0].data = capacities;
    capacityChart.update();

    voltageTempChart.data.labels = cycles;
    voltageTempChart.data.datasets[0].data = voltages;
    voltageTempChart.data.datasets[1].data = temperatures;
    voltageTempChart.update();
}

// ===========================
// ⚡ Обновление текущего статуса
// ===========================
function updateCurrentStatus(latestData) {
    document.getElementById('current-status').innerHTML = `
        <div>Voltage: ${latestData.voltage.toFixed(2)} V</div>
        <div>Current: ${latestData.current.toFixed(2)} A</div>
        <div>Temperature: ${latestData.temperature.toFixed(1)} °C</div>
        <div>Capacity: ${latestData.capacity.toFixed(2)} Ah</div>
    `;
}

// ===========================
// 🤖 Предсказание RUL
// ===========================
async function predictRUL() {
    try {
        const batteryId = 'BATT001';
        const response = await fetch(`${API_BASE}/predict-rul/${batteryId}`);
        const prediction = await response.json();

        document.getElementById('predicted-rul').textContent = `${prediction.predicted_rul} cycles`;
        document.getElementById('confidence-level').textContent = `${(prediction.confidence * 100).toFixed(1)}%`;
        document.getElementById('current-cycle').textContent = `${prediction.current_cycle} cycles`;

    } catch (error) {
        console.error('Error predicting RUL:', error);
    }
}

// ===========================
// 🧪 Добавление sample-данных
// ===========================
async function addSampleData() {
    try {
        const batteryId = 'BATT001';
        const latestData = await getLatestBatteryData(batteryId);
        const nextCycle = latestData ? latestData.cycle_number + 1 : 1;

        const baseCapacity = 100;
        const degradationRate = 0.1;

        const newData = {
            battery_id: batteryId,
            voltage: 3.7 + Math.random() * 0.3,
            current: 2.0 + Math.random() * 0.5,
            temperature: 25 + Math.random() * 10,
            capacity: Math.max(50, baseCapacity - (degradationRate * nextCycle)),
            cycle_number: nextCycle
        };

        const response = await fetch(`${API_BASE}/battery-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(newData)
        });

        if (response.ok) {
            alert('✅ Sample data added successfully!');
            loadBatteryData();
        }

    } catch (error) {
        console.error('Error adding sample data:', error);
    }
}

// ===========================
// 🔍 Получение последних данных
// ===========================
async function getLatestBatteryData(batteryId) {
    try {
        const response = await fetch(`${API_BASE}/battery-history/${batteryId}`);
        const data = await response.json();
        return data.data[data.data.length - 1];
    } catch {
        return null;
    }
}

// ===========================
// 🔁 Переобучение модели
// ===========================
async function retrainModel() {
    try {
        const response = await fetch(`${API_BASE}/retrain-model`, { method: 'POST' });
        const result = await response.json();

        alert(result.success ? '✅ Model retrained successfully!' : '❌ Model retraining failed: ' + result.message);
    } catch (error) {
        console.error('Error retraining model:', error);
    }
}

// ===========================
// 🧾 Обработка формы добавления данных
// ===========================
document.getElementById('battery-data-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const voltage = parseFloat(document.getElementById('voltage').value);
    const current = parseFloat(document.getElementById('current').value);
    const temperature = parseFloat(document.getElementById('temperature').value);
    const capacity = parseFloat(document.getElementById('capacity').value);
    const cycleNumber = parseInt(document.getElementById('cycle-number').value);

    // ⚠️ Проверка допустимых диапазонов
    if (voltage < 2.5 || voltage > 4.5) return alert('⚠️ Voltage must be between 2.5 V and 4.5 V');
    if (current < 0 || current > 10) return alert('⚠️ Current must be between 0 A and 10 A');
    if (temperature < -20 || temperature > 80) return alert('⚠️ Temperature must be between -20 °C and 80 °C');
    if (capacity < 0 || capacity > 120) return alert('⚠️ Capacity must be between 0 Ah and 120 Ah');
    if (cycleNumber < 0 || cycleNumber > 5000) return alert('⚠️ Cycle number must be between 0 and 5000');

    const data = {
        battery_id: document.getElementById('battery-id').value,
        voltage, current, temperature, capacity, cycle_number: cycleNumber
    };

    try {
        const response = await fetch(`${API_BASE}/battery-data`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('✅ Data added successfully!');
            this.reset();
            loadBatteryData();
        } else alert('❌ Error adding data');

    } catch (error) {
        console.error('Error submitting form:', error);
    }
});

// ===========================
// 📘 Help-справочник (ограничения)
// ===========================
function setupHelpTooltip() {
    const helpElement = document.getElementById('help-info');
    if (!helpElement) return;

    helpElement.innerHTML = `
        <h4>📘 Data Entry Guidelines:</h4>
        <ul>
            <li>⚡ <b>Voltage:</b> 2.5 V – 4.5 V</li>
            <li>🔌 <b>Current:</b> 0 A – 10 A</li>
            <li>🌡️ <b>Temperature:</b> -20 °C – 80 °C</li>
            <li>🔋 <b>Capacity:</b> 0 Ah – 120 Ah</li>
            <li>🔁 <b>Cycle Number:</b> 0 – 5000</li>
        </ul>
        <p>Values outside these ranges will be rejected to ensure realistic battery parameters.</p>
    `;
}
