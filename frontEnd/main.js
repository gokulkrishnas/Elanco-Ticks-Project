const API_BASE = 'http://localhost:8432/';

function showResult(elementId, data, isError = false) {
    const element = document.getElementById(elementId);
    if (isError) {
        element.innerHTML = `<div class="error">${data}</div>`;
    } else {
        element.innerHTML = `<div class="results"><pre>${JSON.stringify(data, null, 2)}</pre></div>`;
    }
}

function showLoading(elementId) {
    document.getElementById(elementId).innerHTML = '<div class="loading">Loading...</div>';
}

async function healthCheck() {
    showLoading('health-result');
    try {
        const response = await fetch(`${API_BASE}/`);
        const data = await response.json();
        showResult('health-result', data);
    } catch (error) {
        showResult('health-result', `Error: ${error.message}. Make sure server is running!`, true);
    }
}

async function searchSightings() {
    showLoading('search-result');
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    const location = document.getElementById('location').value;
    const species = document.getElementById('species').value;

    let url = `${API_BASE}/api/sightings/search?`;
    if (startDate) url += `start_date=${startDate}&`;
    if (endDate) url += `end_date=${endDate}&`;
    if (location) url += `location=${location}&`;
    if (species) url += `species=${species}&`;

    try {
        const response = await fetch(url);
        const data = await response.json();
        showResult('search-result', data);
    } catch (error) {
        showResult('search-result', `Error: ${error.message}`, true);
    }
}

function resetFilters() {
    document.getElementById('start-date').value = '';
    document.getElementById('end-date').value = '';
    document.getElementById('location').value = '';
    document.getElementById('species').value = '';
    document.getElementById('search-result').innerHTML = '';
}

async function getRegionStats() {
    showLoading('region-result');
    try {
        const response = await fetch(`${API_BASE}/api/stats/regions`);
        const data = await response.json();
        showResult('region-result', data);
    } catch (error) {
        showResult('region-result', `Error: ${error.message}`, true);
    }
}

async function getTrends(period) {
    showLoading('trends-result');
    try {
        const response = await fetch(`${API_BASE}/api/stats/trends?period=${period}`);
        const data = await response.json();
        showResult('trends-result', data);
    } catch (error) {
        showResult('trends-result', `Error: ${error.message}`, true);
    }
}

async function getSpeciesStats() {
    showLoading('species-result');
    try {
        const response = await fetch(`${API_BASE}/api/stats/species`);
        const data = await response.json();
        showResult('species-result', data);
    } catch (error) {
        showResult('species-result', `Error: ${error.message}`, true);
    }
}

async function getRiskAssessment() {
    showLoading('risk-result');
    try {
        const response = await fetch(`${API_BASE}/api/risk/assessment`);
        const data = await response.json();
        showResult('risk-result', data);
    } catch (error) {
        showResult('risk-result', `Error: ${error.message}`, true);
    }
}

async function getSeasonalPatterns() {
    showLoading('seasonal-result');
    try {
        const response = await fetch(`${API_BASE}/api/patterns/seasonal`);
        const data = await response.json();
        showResult('seasonal-result', data);
    } catch (error) {
        showResult('seasonal-result', `Error: ${error.message}`, true);
    }
}

async function getForecast() {
    showLoading('forecast-result');
    try {
        const response = await fetch(`${API_BASE}/api/forecast/trends`);
        const data = await response.json();
        showResult('forecast-result', data);
    } catch (error) {
        showResult('forecast-result', `Error: ${error.message}`, true);
    }
}

// Load dropdown options
async function loadDropdowns() {
    try {
        const [regions, species] = await Promise.all([
            fetch(`${API_BASE}/api/stats/regions`).then(r => r.json()),
            fetch(`${API_BASE}/api/stats/species`).then(r => r.json())
        ]);

        const locationSelect = document.getElementById('location');
        const speciesSelect = document.getElementById('species');

        if (regions.success) {
            regions.data.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r.location;
                opt.textContent = r.location;
                locationSelect.appendChild(opt);
            });
        }

        if (species.success) {
            species.data.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.species;
                opt.textContent = s.species;
                speciesSelect.appendChild(opt);
            });
        }
    } catch (error) {
        console.error('Error loading dropdowns:', error);
    }
}

window.addEventListener('DOMContentLoaded', loadDropdowns);