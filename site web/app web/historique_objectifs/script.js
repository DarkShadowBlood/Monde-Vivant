document.addEventListener('DOMContentLoaded', () => {
      const startDateInput = document.getElementById('start-date-input');
      const endDateInput = document.getElementById('end-date-input');
      const presetButtons = document.querySelectorAll('.preset-filters button');
      
      const historyGrid = document.getElementById('history-grid');
      const historyTableView = document.getElementById('history-table-view');
      const historyBarChartView = document.getElementById('history-barchart-view');
      const historySummaryView = document.getElementById('history-summary-view');
      const historyTable = document.getElementById('history-table');
      const sortBtn = document.getElementById('sort-btn');
      const barchartTitle = document.getElementById('barchart-title');

      const viewGridBtn = document.getElementById('view-grid-btn');
      const viewTableBtn = document.getElementById('view-table-btn');
      const viewSummaryBtn = document.getElementById('view-summary-btn');
      const viewBarChartPercentBtn = document.getElementById('view-barchart-percent-btn');
      const viewBarChartCaloriesBtn = document.getElementById('view-barchart-calories-btn');
      const viewBarChartStepsBtn = document.getElementById('view-barchart-steps-btn');
      const viewBarChartDistanceBtn = document.getElementById('view-barchart-distance-btn');

      let dailyGoalsData = [];
      let coachPersonalities = {};
      let groupedPersonalities = {};
      let targetValues = { calories: 500, steps: 8000, distance: 5.0 };

      let currentCoachPersonalityKey = 'default';
      let currentView = 'grid';
      let sortOrder = 'desc';
      let currentBarchartMetric = 'percent';

      const parseDateAsLocal = (dateString) => {
        const [year, month, day] = dateString.split('-').map(Number);
        return new Date(year, month - 1, day);
      };

      const getWeekNumber = (d) => {
        d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
        d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
        const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
        return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
      };

      const renderHistory = (startDate, endDate) => {
        const start = parseDateAsLocal(startDate);
        const end = parseDateAsLocal(endDate);
        end.setHours(23, 59, 59, 999);

        let filteredGoals = dailyGoalsData.filter(goal => {
            const goalDate = parseDateAsLocal(goal.date);
            return goalDate >= start && goalDate <= end;
        });

        filteredGoals.sort((a, b) => {
            const dateA = new Date(a.date);
            const dateB = new Date(b.date);
            return sortOrder === 'desc' ? dateB - dateA : dateA - dateB;
        });

        const weeklySummaries = {};
        filteredGoals.forEach(goal => {
            const date = parseDateAsLocal(goal.date);
            const weekId = `${date.getFullYear()}-W${getWeekNumber(date)}`;
            if (!weeklySummaries[weekId]) {
                weeklySummaries[weekId] = { days: [], totals: { calories: 0, steps: 0, distance: 0 }, rawTotals: { calories: 0, steps: 0, distance: 0 }, count: 0 };
            }
            const { percentages, currentValues } = calculatePercentages(goal);
            weeklySummaries[weekId].days.push(goal);
            weeklySummaries[weekId].totals.calories += percentages.calories;
            weeklySummaries[weekId].totals.steps += percentages.steps;
            weeklySummaries[weekId].totals.distance += percentages.distance;
            weeklySummaries[weekId].rawTotals.calories += currentValues.calories;
            weeklySummaries[weekId].rawTotals.steps += currentValues.steps;
            weeklySummaries[weekId].rawTotals.distance += currentValues.distance;
            weeklySummaries[weekId].count++;
        });

        Object.keys(weeklySummaries).forEach(weekId => {
            weeklySummaries[weekId].previousWeekData = getPreviousWeekSummary(weeklySummaries, weekId);
        });

        if (currentView === 'grid') {
            hideBarChart();
            renderGridView(filteredGoals, weeklySummaries);
        } else if (currentView === 'barchart') {
            if (currentBarchartMetric === 'percent') {
              renderPercentBarChartView(filteredGoals);
            } else {
              renderSingleMetricBarChart(filteredGoals, currentBarchartMetric);
            }
        } else if (currentView === 'summary') {
            hideBarChart();
            renderSummaryView(weeklySummaries);
        } else {
            hideBarChart();
            renderTableView(filteredGoals, weeklySummaries);
        }
      };

      const getPercentColor = (percent) => {
        if (percent >= 100) return 'var(--good)';
        if (percent >= 50) return 'var(--medium)';
        return 'var(--bad)';
      };

      const getPercentClass = (percent) => (percent >= 100) ? 'percent-good' : (percent >= 50) ? 'percent-medium' : 'percent-bad';

      const calculatePercentages = (goal) => {
        if (!goal || !goal.calories) return { percentages: { calories: 0, steps: 0, distance: 0 }, currentValues: { calories: 0, steps: 0, distance: 0 } };
        const currentValues = {
            calories: parseFloat(goal.calories.replace(',', '.')) || 0,
            steps: parseInt(goal.steps, 10) || 0,
            distance: parseFloat(goal.distance.replace(',', '.')) || 0,
        };
        const percentages = {
            calories: Math.round((currentValues.calories / targetValues.calories) * 100),
            steps: Math.round((currentValues.steps / targetValues.steps) * 100),
            distance: Math.round((currentValues.distance / targetValues.distance) * 100),
        };
        return { percentages, currentValues };
      };

      const renderGridView = (filteredGoals, weeklySummaries) => {
        hideBarChart();
        historyGrid.innerHTML = '';
        historyTableView.style.display = 'none';
        historySummaryView.style.display = 'none';
        historyGrid.style.display = 'grid';

        if (filteredGoals.length === 0) {
            historyGrid.innerHTML = '<p>Aucune donnée d\'objectif pour la période sélectionnée.</p>';
            return;
        }

        let lastWeekId = null;
        filteredGoals.forEach(goal => {
            const date = parseDateAsLocal(goal.date);
            const weekId = `${date.getFullYear()}-W${getWeekNumber(date)}`;

            if (weekId !== lastWeekId) {
                if (lastWeekId !== null && weeklySummaries[lastWeekId]) {
                    historyGrid.appendChild(createWeeklySummaryCard(weeklySummaries[lastWeekId], lastWeekId, sortOrder));
                }
                lastWeekId = weekId;
            }

            const { percentages, currentValues } = calculatePercentages(goal);

            const card = document.createElement('div');
            card.className = 'day-card';
            card.innerHTML = `
                <h3>${parseDateAsLocal(goal.date).toLocaleDateString('fr-FR', {weekday: 'long', day: 'numeric', month: 'long'})}</h3>
                <div class="goal-grid">
                    <div class="goal-item">
                        <div class="progress-circle" style="background: conic-gradient(${getPercentColor(percentages.calories)} ${Math.min(percentages.calories, 100) * 3.6}deg, var(--border-color) 0deg)"><span class="progress-value ${getPercentClass(percentages.calories)}">${percentages.calories}%</span></div>
                        <div class="goal-label">🔥 Calories</div>
                        <div class="goal-data">${currentValues.calories.toLocaleString('fr-FR')}</div>
                    </div>
                    <div class="goal-item">
                        <div class="progress-circle" style="background: conic-gradient(${getPercentColor(percentages.steps)} ${Math.min(percentages.steps, 100) * 3.6}deg, var(--border-color) 0deg)"><span class="progress-value ${getPercentClass(percentages.steps)}">${percentages.steps}%</span></div>
                        <div class="goal-label">👟 Pas</div>
                        <div class="goal-data">${currentValues.steps.toLocaleString('fr-FR')}</div>
                    </div>
                    <div class="goal-item">
                        <div class="progress-circle" style="background: conic-gradient(${getPercentColor(percentages.distance)} ${Math.min(percentages.distance, 100) * 3.6}deg, var(--border-color) 0deg)"><span class="progress-value ${getPercentClass(percentages.distance)}">${percentages.distance}%</span></div>
                        <div class="goal-label">📏 Distance</div>
                        <div class="goal-data">${currentValues.distance.toFixed(2)} km</div>
                    </div>
                </div>
            `;
            historyGrid.appendChild(card);
        });

        if (lastWeekId !== null && weeklySummaries[lastWeekId]) {
            historyGrid.appendChild(createWeeklySummaryCard(weeklySummaries[lastWeekId], lastWeekId, sortOrder));
        }
      };

      const createWeeklySummaryCard = (summary, weekId, currentSortOrder) => {
        if (!summary) return document.createDocumentFragment();

        const weekDates = summary.days.map(day => parseDateAsLocal(day.date));
        const firstDay = new Date(Math.min.apply(null, weekDates));
        const lastDay = new Date(Math.max.apply(null, weekDates));
        const dateRangeString = `(${firstDay.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short' })} au ${lastDay.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short' })})`;

        const avgPercentages = {
            calories: (summary.totals.calories / summary.count),
            steps: (summary.totals.steps / summary.count),
            distance: (summary.totals.distance / summary.count)
        };

        const weekNumber = weekId.split('-W')[1];

        let comparisonHtml = '';
        const prevWeek = summary.previousWeekData;
        if (prevWeek) {
            const prevAvg = {
                calories: (prevWeek.totals.calories / prevWeek.count),
                steps: (prevWeek.totals.steps / prevWeek.count),
                distance: (prevWeek.totals.distance / prevWeek.count)
            };

            const diffs = {
                calories: avgPercentages.calories - prevAvg.calories,
                steps: avgPercentages.steps - prevAvg.steps,
                distance: avgPercentages.distance - prevAvg.distance
            };

            const formatDiff = (diff) => {
                if (diff > 0) return `<span style="color: var(--good);">(${diff.toFixed(0)}%)</span>`;
                if (diff < 0) return `<span style="color: var(--bad);">(${diff.toFixed(0)}%)</span>`;
                return `<span>(=)</span>`;
            };

            comparisonHtml = `<div class="weekly-summary-details">
                Comparé à S.${prevWeek.weekNumber}: 
                🔥 ${formatDiff(diffs.calories)} | 
                👟 ${formatDiff(diffs.steps)} | 
                📏 ${formatDiff(diffs.distance)}
            </div>`;
        }

        const card = document.createElement('div');
        card.className = 'weekly-summary-card';
        card.innerHTML = `
            <h4>Résumé Semaine ${weekNumber} ${dateRangeString} (Moyenne)</h4>
            <p>Moyenne d'atteinte des objectifs : 
                <b class="${getPercentClass(avgPercentages.calories)}">🔥 ${avgPercentages.calories.toFixed(0)}%</b> | 
                <b class="${getPercentClass(avgPercentages.steps)}">👟 ${avgPercentages.steps.toFixed(0)}%</b> | 
                <b class="${getPercentClass(avgPercentages.distance)}">📏 ${avgPercentages.distance.toFixed(0)}%</b>
            </p>
            ${comparisonHtml}`;
        return card;
      };

      const getPreviousWeekSummary = (allSummaries, currentWeekId) => {
        const [year, week] = currentWeekId.split('-W').map(Number);
        let prevYear = year;
        let prevWeekNum = week - 1;
        if (prevWeekNum < 1) {
            prevWeekNum = 52;
            prevYear--;
        }
        const prevWeekId = `${prevYear}-W${prevWeekNum}`;
        return allSummaries[prevWeekId] ? { ...allSummaries[prevWeekId], weekNumber: prevWeekNum } : null;
      };

      const renderPercentBarChartView = (filteredGoals) => {
        historyGrid.style.display = 'none';
        historyTableView.style.display = 'none';
        historyBarChartView.style.display = 'flex';
        barchartTitle.textContent = "Pourcentage d'atteinte des objectifs";
        barchartTitle.style.display = 'block';

        const container = document.getElementById('barchart-container');
        container.innerHTML = '';
         if (filteredGoals.length === 0) {
            container.innerHTML = '<p>Aucune donnée d\'objectif pour la période sélectionnée.</p>';
            return;
        }

        let minPercent = 100;
        let maxPercent = 0;
        filteredGoals.forEach(goal => {
            const { percentages } = calculatePercentages(goal);
            minPercent = Math.min(minPercent, percentages.calories, percentages.steps, percentages.distance);
            maxPercent = Math.max(maxPercent, percentages.calories, percentages.steps, percentages.distance, 100);
        });

        const scaleMin = Math.floor(minPercent / 5) * 5;
        const scaleMax = Math.ceil(maxPercent / 5) * 5;
        const scaleRange = scaleMax - scaleMin;

        const refLines = new Set();
        refLines.add(scaleMin);
        refLines.add(scaleMax);
        if (scaleMin < 100 && scaleMax > 100) {
          refLines.add(100);
          refLines.add(Math.round(scaleMin + (100 - scaleMin) / 3));
          refLines.add(Math.round(scaleMin + 2 * (100 - scaleMin) / 3));
          refLines.add(Math.round(100 + (scaleMax - 100) / 3));
          refLines.add(Math.round(100 + 2 * (scaleMax - 100) / 3));
        }
        const sortedLines = Array.from(refLines).sort((a, b) => a - b);

        const barContainerHeight = 300 - 10 - 40;
        const yAxisContainer = document.getElementById('yaxis-labels');
        yAxisContainer.innerHTML = '';

        const scrollWidth = container.scrollWidth;
        sortedLines.forEach(value => {
            const positionPercent = (value - scaleMin) / scaleRange;
            const bottomPosition = positionPercent * barContainerHeight;

            const line = document.createElement('div');
            line.className = `reference-line ${value === 100 ? 'goal' : ''}`;
            line.style.bottom = `${bottomPosition + 40}px`;
            container.appendChild(line);

            const label = document.createElement('div');
            label.className = 'yaxis-label';
            label.textContent = `${value}%`;
            label.style.bottom = `${bottomPosition}px`;
            yAxisContainer.appendChild(label);
        });

        filteredGoals.forEach(goal => {
            const { percentages, currentValues } = calculatePercentages(goal);

            const calcHeight = (percent) => {
              const relativePercent = scaleRange > 0 ? (percent - scaleMin) / scaleRange : 0;
              return Math.max(0, relativePercent * barContainerHeight);
            }

            const dayContainer = document.createElement('div');
            dayContainer.className = 'barchart-day';
            dayContainer.innerHTML = `
                <div class="bar" style="height: ${calcHeight(percentages.calories)}px; background-color: ${getPercentColor(percentages.calories)};">
                    <div class="tooltip">🔥 ${currentValues.calories.toLocaleString('fr-FR')} (${percentages.calories}%)</div>
                </div>
                <div class="bar" style="height: ${calcHeight(percentages.steps)}px; background-color: ${getPercentColor(percentages.steps)};">
                    <div class="tooltip">👟 ${currentValues.steps.toLocaleString('fr-FR')} (${percentages.steps}%)</div>
                </div>
                <div class="bar" style="height: ${calcHeight(percentages.distance)}px; background-color: ${getPercentColor(percentages.distance)};">
                    <div class="tooltip">📏 ${currentValues.distance.toFixed(2)}km (${percentages.distance}%)</div>
                </div>
                <div class="barchart-label">${parseDateAsLocal(goal.date).toLocaleDateString('fr-FR', {day: '2-digit', month: '2-digit'})}<br>${parseDateAsLocal(goal.date).toLocaleDateString('fr-FR', {weekday: 'short'})}</div>
            `;
            container.appendChild(dayContainer);
        });
        const finalScrollWidth = container.scrollWidth;
        container.querySelectorAll('.reference-line').forEach(line => {
            line.style.width = `${finalScrollWidth}px`;
        });
      };

      const renderSingleMetricBarChart = (filteredGoals, metric) => {
        historyGrid.style.display = 'none';
        historyTableView.style.display = 'none';
        historyBarChartView.style.display = 'flex';

        const container = document.getElementById('barchart-container');
        container.innerHTML = '';

        if (filteredGoals.length === 0) {
            container.innerHTML = '<p>Aucune donnée d\'objectif pour la période sélectionnée.</p>';
            return;
        }

        const metricConfig = {
          calories: { label: 'Calories (Kcal)', unit: 'Kcal', icon: '🔥', target: targetValues.calories },
          steps: { label: 'Pas', unit: '', icon: '👟', target: targetValues.steps },
          distance_m: { label: 'Distance (mètres)', unit: 'm', icon: '📏', target: targetValues.distance * 1000 }
        };

        barchartTitle.textContent = metricConfig[metric].label;
        barchartTitle.style.display = 'block';

        const dataPoints = filteredGoals.map(goal => {
          const val = parseFloat(goal[metric.replace('_m', '')].replace(',', '.')) || 0;
          return metric === 'distance_m' ? val * 1000 : val;
        });

        let minVal = Math.min(...dataPoints);
        let maxVal = Math.max(...dataPoints);

        const roundToNearest = (value, nearest) => Math.ceil(value / nearest) * nearest;
        
        let rounding;
        if (metric === 'calories') rounding = 50;
        else if (metric === 'steps') rounding = 500;
        else if (metric === 'distance_m') rounding = 500;
        else rounding = 10;

        const scaleMin = Math.floor(minVal / rounding) * rounding;
        const scaleMax = roundToNearest(maxVal, rounding);
        const scaleRange = scaleMax - scaleMin;

        const barContainerHeight = 300 - 10 - 40;
        const yAxisContainer = document.getElementById('yaxis-labels');
        yAxisContainer.innerHTML = '';

        const scrollWidth = container.scrollWidth;
        const step = scaleRange > 0 ? scaleRange / 4 : 0;
        const refLines = [];
        for (let i = 0; i <= 4; i++) {
          refLines.push(Math.round(scaleMin + (step * i)));
        }

        refLines.forEach(value => {
            if (isNaN(value)) return;
            const positionPercent = scaleRange > 0 ? (value - scaleMin) / scaleRange : 0;
            const bottomPosition = positionPercent * barContainerHeight;

            const line = document.createElement('div');
            line.className = 'reference-line';
            line.style.bottom = `${bottomPosition + 40}px`;
            container.appendChild(line);

            const label = document.createElement('div');
            label.className = 'yaxis-label';
            label.textContent = `${value.toLocaleString('fr-FR')}`;
            label.style.bottom = `${bottomPosition}px`;
            yAxisContainer.appendChild(label);
        });

        const targetValue = metricConfig[metric].target;
        if (targetValue > scaleMin && targetValue < scaleMax) {
            const positionPercent = (targetValue - scaleMin) / scaleRange;
            const bottomPosition = positionPercent * barContainerHeight;

            const goalLine = document.createElement('div');
            goalLine.className = 'reference-line goal';
            goalLine.style.bottom = `${bottomPosition + 40}px`;
            container.appendChild(goalLine);

            const goalLabel = document.createElement('div');
            goalLabel.className = 'yaxis-label goal';
            goalLabel.textContent = `${targetValue.toLocaleString('fr-FR')}`;
            goalLabel.style.bottom = `${bottomPosition}px`;
            yAxisContainer.appendChild(goalLabel);
        }

        filteredGoals.forEach((goal, index) => {
            const value = dataPoints[index];
            const relativeValue = (value - scaleMin) / scaleRange;
            const height = scaleRange > 0 ? Math.max(0, relativeValue * barContainerHeight) : 0;
            
            const { percentages } = calculatePercentages(goal);
            const metricForPercent = metric.replace('_m', '');
            const barColor = getPercentColor(percentages[metricForPercent]);

            const dayContainer = document.createElement('div');
            dayContainer.className = 'barchart-day';
            dayContainer.innerHTML = `
                <div class="bar" style="height: ${height}px; background-color: ${barColor};">
                    <div class="tooltip">${metricConfig[metric].icon} ${value.toLocaleString('fr-FR')} ${metricConfig[metric].unit}</div>
                </div>
                <div class="barchart-label">${parseDateAsLocal(goal.date).toLocaleDateString('fr-FR', {day: '2-digit', month: '2-digit'})}<br>${parseDateAsLocal(goal.date).toLocaleDateString('fr-FR', {weekday: 'short'})}</div>
            `;
            container.appendChild(dayContainer);
        });

        const finalScrollWidth = container.scrollWidth;
        container.querySelectorAll('.reference-line').forEach(line => {
            line.style.width = `${finalScrollWidth}px`;
        });
      };

      const hideBarChart = () => {
        historyBarChartView.style.display = 'none';
        barchartTitle.style.display = 'none';
        historySummaryView.style.display = 'none';
      };

      const renderTableView = (filteredGoals, weeklySummaries) => {
        hideBarChart();
        historyTable.innerHTML = '';
        historyGrid.style.display = 'none';
        historyTableView.style.display = 'block';
        historySummaryView.style.display = 'none';

        if (filteredGoals.length === 0) {
            historyTable.innerHTML = '<tbody><tr><td colspan="4">Aucune donnée d\'objectif pour la période sélectionnée.</td></tr></tbody>';
            return;
        }

        const tableHead = `<thead><tr><th>Date</th><th>Calories</th><th>Pas</th><th>Distance</th></tr></thead>`;
        let tableBody = '<tbody>';
        
        let lastWeekId = null;
        filteredGoals.forEach(goal => {
            const date = parseDateAsLocal(goal.date);
            const weekId = `${date.getFullYear()}-W${getWeekNumber(date)}`;

            if (weekId !== lastWeekId) {
                if (lastWeekId !== null && weeklySummaries[lastWeekId]) {
                    tableBody += createWeeklySummaryRow(weeklySummaries[lastWeekId], lastWeekId);
                }
                lastWeekId = weekId;
            }

            const { percentages, currentValues } = calculatePercentages(goal);

            tableBody += `<tr>
                <td>${date.toLocaleDateString('fr-FR', {weekday: 'long', day: 'numeric', month: 'long'})}</td>
                <td>${currentValues.calories.toLocaleString('fr-FR')} <span class="percent-value ${getPercentClass(percentages.calories)}">(${percentages.calories}%)</span></td>
                <td>${currentValues.steps.toLocaleString('fr-FR')} <span class="percent-value ${getPercentClass(percentages.steps)}">(${percentages.steps}%)</span></td>
                <td>${currentValues.distance.toFixed(2)} km <span class="percent-value ${getPercentClass(percentages.distance)}">(${percentages.distance}%)</span></td>
            </tr>`;
        });

        if (lastWeekId && weeklySummaries[lastWeekId]) {
            tableBody += createWeeklySummaryRow(weeklySummaries[lastWeekId], lastWeekId);
        }

        tableBody += '</tbody>';
        historyTable.innerHTML = tableHead + tableBody;
      };

      const renderSummaryView = (weeklySummaries) => {
        historyGrid.style.display = 'none';
        historyBarChartView.style.display = 'none';
        historyTableView.style.display = 'none';
        historySummaryView.style.display = 'grid';
        historySummaryView.innerHTML = '';

        const sortedWeekIds = Object.keys(weeklySummaries).sort((a, b) => {
            const [yearA, weekA] = a.split('-W').map(Number);
            const [yearB, weekB] = b.split('-W').map(Number);
            if (yearA !== yearB) return sortOrder === 'desc' ? yearB - yearA : yearA - yearB;
            return sortOrder === 'desc' ? weekB - weekA : weekA - weekB;
        });

        if (sortedWeekIds.length === 0) {
            historySummaryView.innerHTML = '<p>Aucune donnée hebdomadaire à résumer pour la période sélectionnée.</p>';
            return;
        }

        sortedWeekIds.forEach(weekId => {
            const summary = weeklySummaries[weekId];
            const weekNumber = weekId.split('-W')[1];

            const weekDates = summary.days.map(day => parseDateAsLocal(day.date));
            const firstDay = new Date(Math.min.apply(null, weekDates));
            const lastDay = new Date(Math.max.apply(null, weekDates));
            const dateRangeString = `(${firstDay.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short' })} au ${lastDay.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short' })})`;

            const avgPercentages = {
                calories: summary.totals.calories / summary.count,
                steps: summary.totals.steps / summary.count,
                distance: summary.totals.distance / summary.count,
            };
            const avgRaw = {
                calories: summary.rawTotals.calories / summary.count,
                steps: summary.rawTotals.steps / summary.count,
                distance: summary.rawTotals.distance / summary.count,
            };

            const [year, week] = weekId.split('-W').map(Number);
            let prevYear = year;
            let prevWeekNum = week - 1;
            if (prevWeekNum < 1) {
                prevWeekNum = 52;
                prevYear--;
            }
            const prevWeekId = `${prevYear}-W${prevWeekNum}`;
            const prevSummary = weeklySummaries[prevWeekId];

            let prevAvgPercentages = null;
            let comparisonHtml = { calories: '', steps: '', distance: '' };

            if (prevSummary) {
                const prevAvgPercentages = {
                    calories: prevSummary.totals.calories / prevSummary.count,
                    steps: prevSummary.totals.steps / prevSummary.count,
                    distance: prevSummary.totals.distance / prevSummary.count,
                };
                 const prevAvgRaw = {
                    calories: prevSummary.rawTotals.calories / prevSummary.count,
                    steps: prevSummary.rawTotals.steps / prevSummary.count,
                    distance: prevSummary.rawTotals.distance / prevSummary.count,
                };

                const formatComparison = (current, prev, currentRaw, prevRaw, unit = '', toFixed = 0) => {
                    const diffPercent = current - prev;
                    const diffRaw = currentRaw - prevRaw;
                    const diffClass = diffRaw >= 0 ? 'diff-good' : 'diff-bad';
                    const sign = diffRaw >= 0 ? '+' : '';
                    return `<span class="summary-comparison ${diffClass}">(${sign}${diffPercent.toFixed(0)}% | ${sign}${diffRaw.toLocaleString('fr-FR', {maximumFractionDigits: toFixed})}${unit})</span>`;
                };

                comparisonHtml.calories = formatComparison(avgPercentages.calories, prevAvgPercentages.calories, avgRaw.calories, prevAvgRaw.calories, ' kcal');
                comparisonHtml.steps = formatComparison(avgPercentages.steps, prevAvgPercentages.steps, avgRaw.steps, prevAvgRaw.steps, ' pas');
                comparisonHtml.distance = formatComparison(avgPercentages.distance, prevAvgPercentages.distance, avgRaw.distance, prevAvgRaw.distance, ' km', 2);
            }

            const formatDifference = (currentRaw, target, unit = '', toFixed = 0) => {
                const diff = currentRaw - target;
                const sign = diff >= 0 ? '+' : '';
                const diffClass = diff >= 0 ? 'diff-good' : 'diff-bad';
                return `<span class="summary-comparison ${diffClass}" style="margin-left: 5px;">(${sign}${diff.toLocaleString('fr-FR', {maximumFractionDigits: toFixed})}${unit})</span>`;
            };

            const diffs = {
                calories: formatDifference(avgRaw.calories, targetValues.calories, ' kcal'),
                steps: formatDifference(avgRaw.steps, targetValues.steps, ' pas'),
                distance: formatDifference(avgRaw.distance, targetValues.distance, ' km', 2)
            };

            const coachMessageHtml = getCoachMessage(avgPercentages, prevAvgPercentages);

            const card = document.createElement('div');
            card.className = 'summary-card';
            card.innerHTML = `
                <h3>Résumé Semaine ${weekNumber} ${dateRangeString}</h3>
                <div class="summary-metric">
                    <span class="main-value ${getPercentClass(avgPercentages.calories)}">🔥 ${avgPercentages.calories.toFixed(0)}%</span>
                    <span class="raw-value">(${avgRaw.calories.toFixed(0)} / ${targetValues.calories} kcal)</span>
                    ${diffs.calories}
                    ${comparisonHtml.calories}
                </div>
                <div class="summary-metric">
                    <span class="main-value ${getPercentClass(avgPercentages.steps)}">👟 ${avgPercentages.steps.toFixed(0)}%</span>
                    <span class="raw-value">(${avgRaw.steps.toLocaleString('fr-FR', {maximumFractionDigits: 0})} / ${targetValues.steps.toLocaleString('fr-FR')} pas)</span>
                    ${diffs.steps}
                    ${comparisonHtml.steps}
                </div>
                <div class="summary-metric">
                    <span class="main-value ${getPercentClass(avgPercentages.distance)}">📏 ${avgPercentages.distance.toFixed(0)}%</span>
                    <span class="raw-value">(${avgRaw.distance.toFixed(2)} / ${targetValues.distance.toFixed(1)} km)</span>
                    ${diffs.distance}
                    ${comparisonHtml.distance}
                </div>
                ${coachMessageHtml}`;

            
            historySummaryView.appendChild(card);
        });
      };

      // --- AMÉLIORATION : Chargement simplifié des données ---
      Promise.all([
        fetch('../objectifs.json').then(res => res.json()),
        fetch('coach_engine.json').then(res => res.json())
      ]).then(([goalsData, mainCoachEngine]) => {
        dailyGoalsData = goalsData.sort((a, b) => parseDateAsLocal(b.date) - parseDateAsLocal(a.date));
        
        // Toutes les personnalités sont maintenant dans un seul objet
        coachPersonalities = mainCoachEngine.personalities;

        const savedTargets = JSON.parse(localStorage.getItem('goalTargets'));
        if (savedTargets) {
          targetValues.calories = parseFloat(savedTargets.calories) || 500;
          targetValues.steps = parseInt(savedTargets.steps, 10) || 8000;
          targetValues.distance = parseFloat(savedTargets.distance) || 5.0;
        }

        // Le regroupement par source n'est plus nécessaire car tout est dans un seul fichier.
        // On peut simuler le regroupement si besoin, ou simplement tout afficher.
        // Pour l'instant, on garde la structure pour la compatibilité.
        groupedPersonalities = {};
        const source = mainCoachEngine.llm_source || 'Grok';
        groupedPersonalities[source] = mainCoachEngine.personalities;

        setupCoachControls();
        document.getElementById('filter-last-7').click();

      }).catch(error => console.error("Erreur de chargement des données:", error));

      const createWeeklySummaryRow = (summary, weekId) => {
        if (!summary || summary.days.length === 0) return '';

        const weekDates = summary.days.map(day => parseDateAsLocal(day.date));
        const firstDay = new Date(Math.min.apply(null, weekDates));
        const lastDay = new Date(Math.max.apply(null, weekDates));
        const dateRangeString = `(${firstDay.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short' })} au ${lastDay.toLocaleDateString('fr-CA', { day: 'numeric', month: 'short' })})`;

        const avgCalories = (summary.totals.calories / summary.count).toFixed(0);
        const avgSteps = (summary.totals.steps / summary.count).toFixed(0);
        const avgDistance = (summary.totals.distance / summary.count).toFixed(0);
        const weekNumber = weekId.split('-W')[1];

        return `<tr class="weekly-summary-row">
            <td><b>Résumé S.${weekNumber} ${dateRangeString}</b></td>
            <td><b class="${getPercentClass(avgCalories)}">${avgCalories}%</b></td>
            <td><b class="${getPercentClass(avgSteps)}">${avgSteps}%</b></td>
            <td><b class="${getPercentClass(avgDistance)}">${avgDistance}%</b></td>
        </tr>`;
      };

  const getCoachMessage = (avgPercentages, prevAvgPercentages, monthAgoAvgPercentages) => {
    const personality = coachPersonalities?.[currentCoachPersonalityKey];
    if (!personality || !personality.rules) {
          return '';
        }

    const context = {
      avg: {
        calories: Math.round(avgPercentages.calories),
        steps: Math.round(avgPercentages.steps),
        distance: Math.round(avgPercentages.distance),
        overall: (avgPercentages.calories + avgPercentages.steps + avgPercentages.distance) / 3
      },
      prev_avg: prevAvgPercentages ? {
        calories: Math.round(prevAvgPercentages.calories),
        steps: Math.round(prevAvgPercentages.steps),
        distance: Math.round(prevAvgPercentages.distance),
        overall: (prevAvgPercentages.calories + prevAvgPercentages.steps + prevAvgPercentages.distance) / 3
      } : null
    };
    context.avg.overall = Math.round(context.avg.overall);
    if (context.prev_avg) {
        context.prev_avg.overall = Math.round(context.prev_avg.overall);
      }

    let bestMatch = null;

    for (const rule of personality.rules) {
      try {
        const conditionMet = new Function('avg', 'prev_avg', 'month_ago_avg', 
            `return ${rule.condition}`)(context.avg, context.prev_avg, context.month_ago_avg);

        if (conditionMet) {
          if (!bestMatch || rule.priority > bestMatch.priority) {
            bestMatch = rule;
          }
        }
      } catch (e) {
        if (!e.message.includes("Cannot read properties of null") && !e.message.includes("is not defined")) {
            console.error(`Erreur dans la condition de la règle '${rule.id}':`, e);
        }
      }
        }

    const messages = bestMatch ? bestMatch.texts : personality.default;
        if (!messages || messages.length === 0) return '';

        const randomIndex = Math.floor(Math.random() * messages.length);
        let message = messages[randomIndex];

        message = message.replace(/\{([^}]+)\}/g, (match, p1) => {
            try {
                return new Function('context', `return context.${p1}`)(context) ?? match;
            } catch (e) {
                return match;
            }
        });
        return `<div class="coach-message">${message}</div>`;
      };

  const setupCoachControls = () => {
    const container = document.getElementById('coach-controls');
    if (!container || Object.keys(groupedPersonalities).length === 0) return;
    container.innerHTML = '';

    const llmSelectorContainer = document.createElement('div');
    llmSelectorContainer.id = 'llm-selector-container';

    const personalitySelectorContainer = document.createElement('div');
    personalitySelectorContainer.id = 'personality-selector-container';

    const renderPersonalityButtons = (source) => {
        personalitySelectorContainer.innerHTML = '';
        const personalities = groupedPersonalities[source];
        if (!personalities) return;

        Object.keys(personalities).forEach(key => {
            const personality = personalities[key];
            const button = document.createElement('button');
            button.textContent = personality.name;
            button.dataset.key = key;
            if (key === currentCoachPersonalityKey) {
                button.classList.add('active');
            }
            button.addEventListener('click', () => {
                currentCoachPersonalityKey = key;
                document.querySelectorAll('#personality-selector-container button').forEach(btn => btn.classList.remove('active'));
                button.classList.add('active');
                triggerUpdate();
            });
            personalitySelectorContainer.appendChild(button);
        });
    };

    Object.keys(groupedPersonalities).forEach((source, index) => {
        const button = document.createElement('button');
        button.textContent = source;
        button.dataset.source = source;
        if (index === 0) {
            button.classList.add('active');
        }
        button.addEventListener('click', () => {
            llmSelectorContainer.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            renderPersonalityButtons(source);
        });
        llmSelectorContainer.appendChild(button);
    });

    container.appendChild(llmSelectorContainer);
    container.appendChild(personalitySelectorContainer);

    const firstSource = Object.keys(groupedPersonalities)[0];
    if (firstSource) {
        renderPersonalityButtons(firstSource);
    }
  };

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

      const setActiveButton = (activeBtn) => {
        presetButtons.forEach(btn => btn.classList.remove('active'));
        if (activeBtn) activeBtn.classList.add('active');
      };

      presetButtons.forEach(button => {
        button.addEventListener('click', () => {
          setActiveButton(button);
          const today = new Date();
          let start, end = new Date();

          switch(button.id) {
            case 'filter-this-month':
              start = new Date(today.getFullYear(), today.getMonth(), 1);
              end = new Date(today.getFullYear(), today.getMonth() + 1, 0);
              break;
            case 'filter-last-30':
              start = new Date();
              start.setDate(today.getDate() - 29);
              break;
            case 'filter-last-7':
            default:
              start = new Date();
              start.setDate(today.getDate() - 6);
              break;
            case 'filter-last-3-months':
              end = new Date();
              start = new Date();
              start.setMonth(end.getMonth() - 3);
              break;
            case 'filter-last-6-months':
              end = new Date();
              start = new Date();
              start.setMonth(end.getMonth() - 6);
              break;
            case 'filter-all':
              if (dailyGoalsData.length > 0) {
                  start = parseDateAsLocal(dailyGoalsData[dailyGoalsData.length - 1].date);
                  end = parseDateAsLocal(dailyGoalsData[0].date);
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

      const handleViewButtonClick = (view, metric = null) => {
        currentView = view;
        currentBarchartMetric = metric;

        document.querySelectorAll('.view-controls button').forEach(b => b.classList.remove('active'));
        
        let activeBtnId;
        if (view === 'grid') activeBtnId = 'view-grid-btn';
        else if (view === 'table') activeBtnId = 'view-table-btn';
        else if (view === 'summary') activeBtnId = 'view-summary-btn';
        else if (view === 'barchart') {
            activeBtnId = `view-barchart-${metric.replace('_m', '')}-btn`;
        }
        if (activeBtnId) document.getElementById(activeBtnId).classList.add('active');

        const coachControls = document.getElementById('coach-controls');
        if (coachControls) {
            if (view === 'summary') {
                coachControls.style.display = 'flex';
            } else {
                coachControls.style.display = 'none';
            }
        }

        triggerUpdate();
      };

      viewGridBtn.addEventListener('click', () => handleViewButtonClick('grid'));
      viewTableBtn.addEventListener('click', () => handleViewButtonClick('table'));
      viewSummaryBtn.addEventListener('click', () => handleViewButtonClick('summary'));
      viewBarChartPercentBtn.addEventListener('click', () => handleViewButtonClick('barchart', 'percent'));
      viewBarChartCaloriesBtn.addEventListener('click', () => handleViewButtonClick('barchart', 'calories'));
      viewBarChartStepsBtn.addEventListener('click', () => handleViewButtonClick('barchart', 'steps'));
      viewBarChartDistanceBtn.addEventListener('click', () => handleViewButtonClick('barchart', 'distance_m'));
    });
