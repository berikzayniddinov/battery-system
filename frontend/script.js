const API_BASE = 'http://localhost:8000/api';
let capacityChart, voltageTempChart;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeCharts();
    loadBatteryData();
    setInterval(loadBatteryData, 30000); // Обновление каждые 30 секунд
});

// Инициализация графиков
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
                title: {
                    display: true,
                    text: 'Capacity Degradation Over Time'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Cycle Number'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Capacity (Ah)'
                    }
                }
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
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Voltage and Temperature Over Time'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Cycle Number'
                    }
                },
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                    title: {
                        display: true,
                        text: 'Voltage (V)'
                    }
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    title: {
                        display: true,
                        text: 'Temperature (°C)'
                    },
                    grid: {
                        drawOnChartArea: false,
                    },
                }
            }
        }
    });
}

// Загрузка данных батареи
async function loadBatteryData() {
    try {
        const batteryId = 'BATT001';

        // Загрузка исторических данных
        const historyResponse = await fetch(`${API_BASE}/battery-history/${batteryId}`);
        const historyData = await historyResponse.json();

        if (historyData.data && historyData.data.length > 0) {
            updateCharts(historyData.data);
            updateCurrentStatus(historyData.data[historyData.data.length - 1]);
        }

        // Получение предсказания
        await predictRUL();

    } catch (error) {
        console.error('Error loading battery data:', error);
        document.getElementById('current-status').textContent = 'Error loading data';
    }
}

// Обновление графиков
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

// Обновление текущего статуса
function updateCurrentStatus(latestData) {
    document.getElementById('current-status').innerHTML = `
        <div>Voltage: ${latestData.voltage} V</div>
        <div>Current: ${latestData.current} A</div>
        <div>Temperature: ${latestData.temperature} °C</div>
        <div>Capacity: ${latestData.capacity} Ah</div>
    `;
}

// Предсказание RUL
async function predictRUL() {
    try {
        const batteryId = 'BATT001';
        const response = await fetch(`${API_BASE}/predict-rul/${batteryId}`);
        const prediction = await response.json();

        document.getElementById('predicted-rul').textContent =
            `${prediction.predicted_rul} cycles`;
        document.getElementById('confidence-level').textContent =
            `${(prediction.confidence * 100).toFixed(1)}%`;
        document.getElementById('current-cycle').textContent =
            `${prediction.current_cycle} cycles`;

    } catch (error) {
        console.error('Error predicting RUL:', error);
    }
}

// Добавление sample данных
async function addSampleData() {
    try {
        const batteryId = 'BATT001';
        const latestData = await getLatestBatteryData(batteryId);
        const nextCycle = latestData ? latestData.cycle_number + 1 : 1;

        // Генерация реалистичных данных с деградацией
        const baseCapacity = 100; // Начальная емкость
        const degradationRate = 0.1; // Деградация за цикл

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
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(newData)
        });

        if (response.ok) {
            alert('Sample data added successfully!');
            loadBatteryData();
        }

    } catch (error) {
        console.error('Error adding sample data:', error);
    }
}

// Получение последних данных батареи
async function getLatestBatteryData(batteryId) {
    try {
        const response = await fetch(`${API_BASE}/battery-history/${batteryId}`);
        const data = await response.json();
        return data.data[data.data.length - 1];
    } catch (error) {
        return null;
    }
}

// Переобучение модели
async function retrainModel() {
    try {
        const response = await fetch(`${API_BASE}/retrain-model`, {
            method: 'POST'
        });
        const result = await response.json();

        if (result.success) {
            alert('Model retrained successfully!');
        } else {
            alert('Model retraining failed: ' + result.message);
        }

    } catch (error) {
        console.error('Error retraining model:', error);
    }
}

// Обработка формы добавления данных
document.getElementById('battery-data-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const data = {
        battery_id: document.getElementById('battery-id').value,
        voltage: parseFloat(document.getElementById('voltage').value),
        current: parseFloat(document.getElementById('current').value),
        temperature: parseFloat(document.getElementById('temperature').value),
        capacity: parseFloat(document.getElementById('capacity').value),
        cycle_number: parseInt(document.getElementById('cycle-number').value)
    };

    try {
        const response = await fetch(`${API_BASE}/battery-data`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Data added successfully!');
            this.reset();
            loadBatteryData();
        } else {
            alert('Error adding data');
        }

    } catch (error) {
        console.error('Error submitting form:', error);
    }
});