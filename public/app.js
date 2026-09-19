const API_BASE = '/api';

let currentFareClass = 'Economy';

// Plotly Dark Theme Layout Template
const plotlyLayout = {
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    font: { family: 'Inter, sans-serif', color: '#94a3b8' },
    margin: { t: 20, r: 20, l: 40, b: 40 },
    xaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' },
    yaxis: { gridcolor: 'rgba(255,255,255,0.05)', zerolinecolor: 'rgba(255,255,255,0.1)' }
};

async function fetchAPI(endpoint) {
    try {
        const res = await fetch(`${API_BASE}${endpoint}`);
        return await res.json();
    } catch (e) {
        console.error(`Error fetching ${endpoint}:`, e);
        return null;
    }
}

async function initDashboard() {
    // Fetch Data
    const [indexData, pricesData] = await Promise.all([
        fetchAPI('/index/daily'),
        fetchAPI(`/prices?fare_class=${encodeURIComponent(currentFareClass)}`)
    ]);

    if (!indexData || !pricesData) return;

    // 1. Update KPIs
    document.getElementById('val-apix').textContent = indexData.current_apix ? indexData.current_apix.toFixed(2) : '--';
    document.getElementById('val-mospi').textContent = indexData.official_mospi_apix;
    
    if (indexData.current_apix) {
        const apixVar = ((indexData.current_apix - indexData.official_mospi_apix) / indexData.official_mospi_apix) * 100;
        const apixEl = document.getElementById('val-apix-var');
        apixEl.textContent = `${apixVar > 0 ? '+' : ''}${apixVar.toFixed(2)}%`;
        apixEl.style.color = apixVar > 0 ? 'var(--red)' : 'var(--green)';
    }

    document.getElementById('val-routes').textContent = `${indexData.routes_mapped} / ${indexData.total_basket}`;

    // Calculate Overall Fare Variance
    let totalScraped = 0;
    let totalDgca = 0;
    pricesData.forEach(d => {
        if (d.scraped_avg && d.dgca_avg) {
            totalScraped += d.scraped_avg;
            totalDgca += d.dgca_avg;
        }
    });

    if (totalDgca > 0) {
        const fareVar = ((totalScraped - totalDgca) / totalDgca) * 100;
        const fareEl = document.getElementById('val-fare-var');
        fareEl.textContent = `${fareVar > 0 ? '+' : ''}${fareVar.toFixed(2)}%`;
        fareEl.style.color = fareVar > 0 ? 'var(--red)' : 'var(--green)';
    } else {
        document.getElementById('val-fare-var').textContent = '--%';
        document.getElementById('val-fare-var').style.color = '#fff';
    }

    // 2. Timeline Chart
    const dates = indexData.history.map(d => d.date);
    const apixValues = indexData.history.map(d => d.apix);
    const mospiValues = indexData.history.map(() => indexData.official_mospi_apix);

    Plotly.newPlot('chart-timeline', [
        {
            x: dates, y: apixValues, 
            type: 'scatter', mode: 'lines+markers', 
            name: 'APIx', 
            line: { color: '#38bdf8', width: 3, shape: 'spline' },
            marker: { size: 8 }
        },
        {
            x: dates, y: mospiValues, 
            type: 'scatter', mode: 'lines', 
            name: 'MoSPI Benchmark', 
            line: { color: '#94a3b8', width: 2, dash: 'dash' }
        }
    ], { ...plotlyLayout, hovermode: 'x unified', legend: { orientation: 'h', y: -0.2 } }, { responsive: true });

    // 2.5 Route Indices Chart
    if (indexData.route_indices) {
        // We only show routes that actually have an index calculated
        const calculatedRoutes = Object.keys(indexData.route_indices);
        // Sort by index descending
        calculatedRoutes.sort((a, b) => indexData.route_indices[b] - indexData.route_indices[a]);
        
        const routeIdxVals = calculatedRoutes.map(r => indexData.route_indices[r]);
        
        Plotly.newPlot('chart-route-indices', [{
            x: calculatedRoutes,
            y: routeIdxVals,
            type: 'bar',
            marker: { color: '#8b5cf6' }
        }], { 
            ...plotlyLayout,
            margin: { t: 20, r: 20, l: 40, b: 120 }, // extra bottom margin for route names
            yaxis: { title: 'Index (Base = 100)' }
        }, { responsive: true });
    }

    // 3. Heatmap
    // Filter routes that have scraped data
    const validPrices = pricesData.filter(d => d.scraped_avg !== null);
    
    // Sort by variance
    validPrices.sort((a, b) => b.variance_pct - a.variance_pct);
    
    const routes = validPrices.map(d => d.route);
    const variances = validPrices.map(d => [d.variance_pct]);

    // Use a diverging color scale (Green for negative variance, Red for positive)
    Plotly.newPlot('chart-heatmap', [{
        z: variances,
        y: routes,
        x: ['Variance %'],
        type: 'heatmap',
        colorscale: [
            [0, '#10b981'], // Green (Cheaper)
            [0.5, '#1e293b'], // Neutral (Dark)
            [1, '#ef4444']  // Red (Surge)
        ],
        zmin: -50, zmax: 50,
        hoverongaps: false
    }], { 
        ...plotlyLayout, 
        margin: { t: 20, r: 20, l: 140, b: 20 },
        yaxis: { automargin: true }
    }, { responsive: true });

    // 4. Elasticity Setup
    const select = document.getElementById('route-select');
    select.innerHTML = '';
    pricesData.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.route;
        opt.textContent = d.route;
        select.appendChild(opt);
    });

    select.removeEventListener('change', handleElasticityChange);
    select.addEventListener('change', handleElasticityChange);
    
    // Load first route elasticity if exists
    if (pricesData.length > 0) {
        loadElasticity(pricesData[0].route);
    } else {
        Plotly.purge('chart-elasticity');
    }
}

function handleElasticityChange(e) {
    loadElasticity(e.target.value);
}

async function loadElasticity(route) {
    const data = await fetchAPI(`/elasticity?route=${route}&fare_class=${encodeURIComponent(currentFareClass)}`);
    if (!data || !data.data) return;

    const windows = data.data.map(d => `T+${d.window}`);
    const fares = data.data.map(d => d.avg_fare);

    Plotly.newPlot('chart-elasticity', [{
        x: windows,
        y: fares,
        type: 'scatter',
        mode: 'lines+markers',
        line: { color: '#6366f1', width: 3, shape: 'spline' },
        marker: { size: 10, color: '#818cf8' },
        fill: 'tozeroy',
        fillcolor: 'rgba(99, 102, 241, 0.1)'
    }], { 
        ...plotlyLayout,
        xaxis: { title: 'Advance Purchase Window', ...plotlyLayout.xaxis },
        yaxis: { title: 'Average Total Fare (₹)', ...plotlyLayout.yaxis }
    }, { responsive: true });
}

// Global Fare Class Change
document.getElementById('global-fare-class').addEventListener('change', (e) => {
    currentFareClass = e.target.value;
    initDashboard(); // Re-fetch and re-render everything
});

// Boot
initDashboard();
