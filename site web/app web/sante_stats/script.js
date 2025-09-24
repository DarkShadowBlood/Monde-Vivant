document.addEventListener('DOMContentLoaded', () => {
    const startDateInput = document.getElementById('start-date-input');
    const endDateInput = document.getElementById('end-date-input');
    const presetButtons = document.querySelectorAll('.preset-filters button');
    const metricButtons = document.querySelectorAll('.metric-controls button');
    const viewButtons = document.querySelectorAll('.view-controls button');
    const chartCanvas = document.getElementById('health-chart');

    const chartView = document.getElementById('chart-view');
    const tableView = document.getElementById('history-table-view');
    const summaryView = document.getElementById('history-summary-view');
    const historyTable = document.getElementById('history-table');

    let healthData = [];
    let healthChart = null;
    let currentMetric = 'weight'; // 'weight', 'waist', 'glycemie'
    let currentView = 'chart'; // 'chart', 'table', 'summary'
    let sortOrder = 'desc';

    const metricConfig = {
        weight: { label: 'Poids (lb)', key: 'weight.value', color: '#4CAF50' },
        waist: { label: 'Tour de taille (cm)', key: 'waist.value', color: '#2196F3' },
        glycemie: { label: 'Glycémie (mmol/L)', key: 'glycemie_mmol_l', color: '#f44336' }
    };

    const parseDateAsLocal = (dateString) => {
        if (!dateString) return null;
        const [year, month, day] = dateString.split('-').map(Number);
        return new Date(year, month - 1, day);
    };

    const getWeekNumber = (d) => {
        d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    };

    const getValue = (obj, path) => path.split('.').reduce((acc, part) => acc && acc[part], obj);

    const renderHistory = (startDate, endDate) => {
        const start = parseDateAsLocal(startDate);
        const end = parseDateAsLocal(endDate);
        if (!start || !end) return;
        end.setHours(23, 59, 59, 999);

        const filteredData = healthData.filter(item => {
            const itemDate = parseDateAsLocal(item.date);
            return itemDate >= start && itemDate <= end;
        });

        filteredData.sort((a, b) => {
            const dateA = parseDateAsLocal(a.date);
            const dateB = parseDateAsLocal(b.date);
            return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });

        chartView.style.display = 'none';
        tableView.style.display = 'none';
        summaryView.style.display = 'none';

        switch (currentView) {
            case 'chart':
                chartView.style.display = 'block';
                updateChart(filteredData);
                break;
            case 'table':
                tableView.style.display = 'block';
                renderTableView(filteredData);
                break;
            case 'summary':
                summaryView.style.display = 'grid';
                renderSummaryView(filteredData);
                break;
        }
    };

    const renderTableView = (data) => {
        let tableBody = '<tbody>';
        const tableHead = `<thead><tr><th>Date</th><th>Poids (lb)</th><th>Taille (cm)</th><th>Glycémie (mmol/L)</th></tr></thead>`;

        if (data.length === 0) {
            tableBody += '<tr><td colspan="4">Aucune donnée pour la période sélectionnée.</td></tr>';
        } else {
            data.forEach(item => {
                tableBody += `<tr>
                    <td>${parseDateAsLocal(item.date).toLocaleDateString('fr-FR', {weekday: 'long', day: 'numeric', month: 'long'})}</td>
                    <td>${getValue(item, 'weight.value') || '-'}</td>
                    <td>${getValue(item, 'waist.value') || '-'}</td>
                    <td>${item.glycemie_mmol_l || '-'}</td>
                </tr>`;
            });
        }
        tableBody += '</tbody>';
        historyTable.innerHTML = tableHead + tableBody;
    };

    const renderSummaryView = (data) => {
        summaryView.innerHTML = '';
        if (data.length === 0) {
            summaryView.innerHTML = '<p>Aucune donnée à résumer pour la période sélectionnée.</p>';
            return;
        }

        const weeklySummaries = {};
        data.forEach(item => {
            const date = parseDateAsLocal(item.date);
            const weekId = `${date.getFullYear()}-W${getWeekNumber(date)}`;
            if (!weeklySummaries[weekId]) {
                weeklySummaries[weekId] = { days: [], weight: [], waist: [], glycemie: [] };
            }
            weeklySummaries[weekId].days.push(item);
            const weight = getValue(item, 'weight.value');
            const waist = getValue(item, 'waist.value');
            if (weight) weeklySummaries[weekId].weight.push(weight);
            if (waist) weeklySummaries[weekId].waist.push(waist);
            if (item.glycemie_mmol_l) weeklySummaries[weekId].glycemie.push(item.glycemie_mmol_l);
        });

        const sortedWeekIds = Object.keys(weeklySummaries).sort((a, b) => {
            const [yearA, weekA] = a.split('-W').map(Number);
            const [yearB, weekB] = b.split('-W').map(Number);
            if (yearA !== yearB) return sortOrder === 'desc' ? yearB - yearA : yearA - yearB;
            return sortOrder === 'desc' ? weekB - weekA : weekA - weekB;
        });

        sortedWeekIds.forEach(weekId => {
            const summary = weeklySummaries[weekId];
            const weekNumber = weekId.split('-W')[1];

            const avg = (arr) => arr.length > 0 ? (arr.reduce((a, b) => a + b, 0) / arr.length) : 0;
            const avgWeight = avg(summary.weight);
            const avgWaist = avg(summary.waist);
            const avgGlycemie = avg(summary.glycemie);

            const card = document.createElement('div');
            card.className = 'summary-card'; // You might need to add styles for this class
            card.innerHTML = `
                <h3>Résumé Semaine ${weekNumber}</h3>
                <div class="summary-metric">
                    <span class="main-value">⚖️ Poids: ${avgWeight > 0 ? avgWeight.toFixed(1) + ' lb' : '-'}</span>
                </div>
                <div class="summary-metric">
                    <span class="main-value">📏 Tour de taille: ${avgWaist > 0 ? avgWaist.toFixed(1) + ' cm' : '-'}</span>
                </div>
                <div class="summary-metric">
                    <span class="main-value">🩸 Glycémie: ${avgGlycemie > 0 ? avgGlycemie.toFixed(1) + ' mmol/L' : '-'}</span>
                </div>
            `;
            summaryView.appendChild(card);
        });
    };


    const updateChart = (data) => {
        const config = metricConfig[currentMetric];
        const labels = data.map(d => d.date).sort((a,b) => parseDateAsLocal(a) - parseDateAsLocal(b));
        const chartData = labels.map(label => {
            const dayData = data.find(d => d.date === label);
            return dayData ? getValue(dayData, config.key) || null : null;
        });


        if (healthChart) {
            healthChart.data.labels = labels;
            healthChart.data.datasets[0].label = config.label;
            healthChart.data.datasets[0].data = chartData;
            healthChart.data.datasets[0].borderColor = config.color;
            healthChart.data.datasets[0].backgroundColor = `${config.color}33`;
            healthChart.data.datasets[0].pointBackgroundColor = config.color;
            healthChart.options.scales.y.title.text = config.label;
            healthChart.update();
        } else {
            const ctx = chartCanvas.getContext('2d');
            healthChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: config.label,
                        data: chartData,
                        borderColor: config.color,
                        backgroundColor: `${config.color}33`,
                        borderWidth: 2,
                        pointBackgroundColor: config.color,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        tension: 0.1,
                        spanGaps: true
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                        y: {
                            beginAtZero: false,
                            ticks: { color: '#a0a0a0' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            title: { display: true, text: config.label, color: '#f0f0f0' }
                        }
                    }
                }
            });
        }
    };

    // --- Initialisation ---
    fetch('../sante.json')
        .then(res => res.json())
        .then(data => {
            healthData = data;
            document.getElementById('filter-last-30').click();
        })
        .catch(error => {
            console.error("Erreur de chargement des données de santé:", error);
            document.querySelector('.history-container').innerHTML += `<p style="color: #e53935;">Erreur: Impossible de charger les données de santé.</p>`;
        });

    // --- Event Listeners ---
    const datepickerOptions = { format: 'yyyy-mm-dd', language: 'fr', autohide: true, todayHighlight: true };
    const startDatepicker = new Datepicker(startDateInput, datepickerOptions);
    const endDatepicker = new Datepicker(endDateInput, datepickerOptions);

    const triggerUpdate = () => {
        const start = startDatepicker.getDate('yyyy-mm-dd');
        const end = endDatepicker.getDate('yyyy-mm-dd');
        if (start && end) {
            renderHistory(start, end);
        }
    };

    startDateInput.addEventListener('changeDate', triggerUpdate);
    endDateInput.addEventListener('changeDate', triggerUpdate);

    const setActiveButton = (activeBtn, buttons) => {
        buttons.forEach(btn => btn.classList.remove('active'));
        if (activeBtn) activeBtn.classList.add('active');
    };

    presetButtons.forEach(button => {
        button.addEventListener('click', () => {
            setActiveButton(button, presetButtons);
            const today = new Date();
            let start, end = new Date();
            switch(button.id) {
                case 'filter-this-month':
                    start = new Date(today.getFullYear(), today.getMonth(), 1);
                    end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
                    break;
                case 'filter-last-30':
                    start = new Date(); start.setDate(today.getDate() - 29);
                    break;
                case 'filter-last-7':
                    start = new Date(); start.setDate(today.getDate() - 6);
                    break;
                case 'filter-last-3-months':
                    start = new Date(); start.setMonth(today.getMonth() - 3);
                    break;
                case 'filter-last-6-months':
                    start = new Date(); start.setMonth(today.getMonth() - 6);
                    break;
                case 'filter-all':
                    if (healthData.length > 0) {
                        const sortedDates = healthData.map(d => parseDateAsLocal(d.date)).sort((a,b) => a - b);
                        start = sortedDates[0];
                        end = sortedDates[sortedDates.length - 1];
                    } else {
                        start = new Date(); end = new Date();
                    }
                    break;
            }
            startDatepicker.setDate(start);
            endDatepicker.setDate(end);
            triggerUpdate();
        });
    });

    metricButtons.forEach(button => {
        button.addEventListener('click', () => {
            setActiveButton(button, metricButtons);
            if (button.id === 'view-weight-btn') currentMetric = 'weight';
            if (button.id === 'view-waist-btn') currentMetric = 'waist';
            if (button.id === 'view-glycemie-btn') currentMetric = 'glycemie';
            triggerUpdate();
        });
    });

    viewButtons.forEach(button => {
        button.addEventListener('click', () => {
            setActiveButton(button, viewButtons);
            if (button.id === 'view-chart-btn') currentView = 'chart';
            if (button.id === 'view-table-btn') currentView = 'table';
            if (button.id === 'view-summary-btn') currentView = 'summary';
            triggerUpdate();
        });
    });
});