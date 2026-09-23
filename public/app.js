/**
 * Taiwan Weather Forecast - The Powerpuff Girls Edition (飛天小女警特派氣象站)
 * Handles data fetching, Chart.js dual spline curves, clean watermark-free OpenStreetMap,
 * and automatic self-updating cycles.
 */

// Application State
const state = {
  currentRegion: '臺北市',
  regions: [],
  selectedForecasts: [],
  mapPoints: [],
  lastSync: '',
  chartInstance: null,
  mapInstance: null,
  markersLayer: null,
  isSyncing: false,
  autoRefreshInterval: null
};

// Weekday helper (Traditional Chinese)
const WEEKDAYS = ['週日', '週一', '週二', '週三', '週四', '週五', '週六'];

function formatWeekday(dateStr) {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    return WEEKDAYS[d.getDay()];
  } catch (e) {
    return '';
  }
}

function formatDateShort(dateStr) {
  try {
    const parts = dateStr.split('-');
    if (parts.length === 3) {
      return `${parseInt(parts[1], 10)}/${parseInt(parts[2], 10)}`;
    }
    return dateStr;
  } catch (e) {
    return dateStr;
  }
}

// Weather icon selector based on temp & conditions
function getWeatherIcon(mint, maxt, index) {
  const avg = (mint + maxt) / 2;
  if (avg >= 31) return { icon: '☀️', desc: '晴朗炎熱 🌸' };
  if (avg >= 28) return { icon: '⛅', desc: '多雲時晴 💖' };
  if (avg >= 24) return { icon: '🌤️', desc: '晴時多雲 🫧' };
  if (avg >= 20) return { icon: '☁️', desc: '陰天多雲 ⚡' };
  return { icon: '🌧️', desc: '短暫陣雨 ☔' };
}

// Toast notification helper (Powerpuff Girls Theme)
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === 'success' ? '💖' : type === 'error' ? '⚡' : '🌸'}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// ============================================================================
// 1. Data Fetching & Sync
// ============================================================================
async function fetchWeatherData(region = null, triggerSync = false) {
  try {
    let url = '/api/weather';
    const params = new URLSearchParams();
    if (region) params.append('region', region);
    if (triggerSync) params.append('sync', '1');
    if (Array.from(params).length > 0) {
      url += '?' + params.toString();
    }

    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();

    if (data.status === 'success') {
      state.lastSync = data.last_sync || '';
      state.regions = data.regions || [];
      state.currentRegion = data.selected_region || region || '臺北市';
      state.selectedForecasts = data.selected_forecasts || [];
      state.mapPoints = data.map_points || [];

      if (data.sync_message) {
        showToast(data.sync_message, 'success');
      }

      renderAll();
    } else {
      throw new Error(data.message || '無法取得氣象資料');
    }
  } catch (err) {
    console.warn('API fetch failed, falling back to cached state:', err);
    if (triggerSync) {
      showToast('氣象署連線中，已即時為您載入快取資料！', 'info');
    }
  }
}

// ============================================================================
// 2. Rendering Controllers
// ============================================================================
function renderAll() {
  renderSyncInfo();
  renderRegionControls();
  renderKeyMetrics();
  renderForecastCards();
  renderSplineChart();
  renderMapMarkers();
  renderDataTable();
}

function renderSyncInfo() {
  const timeEl = document.getElementById('last-sync-time');
  if (timeEl) {
    timeEl.textContent = `最後同步時間：${state.lastSync || '剛剛'}`;
  }
}

function renderRegionControls() {
  const select = document.getElementById('region-select');
  if (select && select.options.length <= 1) {
    select.innerHTML = '';
    state.regions.forEach(reg => {
      const opt = document.createElement('option');
      opt.value = reg;
      opt.textContent = reg;
      opt.selected = (reg === state.currentRegion);
      select.appendChild(opt);
    });
  } else if (select) {
    select.value = state.currentRegion;
  }

  // Update pill active classes
  document.querySelectorAll('.pill-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.region === state.currentRegion);
  });

  const regionTitle = document.getElementById('forecast-region-name');
  if (regionTitle) regionTitle.textContent = state.currentRegion;

  const metricRegion = document.getElementById('metric-region-tag');
  if (metricRegion) metricRegion.textContent = state.currentRegion;
}

function renderKeyMetrics() {
  const forecasts = state.selectedForecasts;
  if (!forecasts || forecasts.length === 0) return;

  let sumAvg = 0;
  let maxTemp = -999;
  let maxDate = '';
  let minTemp = 999;
  let minDate = '';
  let maxDiff = 0;

  forecasts.forEach(f => {
    const mint = parseFloat(f.mint);
    const maxt = parseFloat(f.maxt);
    const avg = (mint + maxt) / 2;
    const diff = maxt - mint;

    sumAvg += avg;
    if (maxt > maxTemp) {
      maxTemp = maxt;
      maxDate = f.dataDate;
    }
    if (mint < minTemp) {
      minTemp = mint;
      minDate = f.dataDate;
    }
    if (diff > maxDiff) {
      maxDiff = diff;
    }
  });

  const avgOverall = (sumAvg / forecasts.length).toFixed(1);

  document.getElementById('metric-avg').textContent = avgOverall;
  document.getElementById('metric-max').textContent = maxTemp.toFixed(1);
  document.getElementById('metric-max-date').textContent = `${formatDateShort(maxDate)} (${formatWeekday(maxDate)})`;
  document.getElementById('metric-min').textContent = minTemp.toFixed(1);
  document.getElementById('metric-min-date').textContent = `${formatDateShort(minDate)} (${formatWeekday(minDate)})`;
  document.getElementById('metric-diff').textContent = maxDiff.toFixed(1);
}

// ----------------------------------------------------------------------------
// Fix Issue 1: 今日氣溫絕不遮擋 (Natural vertical flow with clean tag pill)
// ----------------------------------------------------------------------------
function renderForecastCards() {
  const container = document.getElementById('forecast-cards');
  if (!container) return;

  container.innerHTML = '';
  const forecasts = state.selectedForecasts;

  const todayStr = new Date().toISOString().slice(0, 10);

  forecasts.forEach((f, idx) => {
    const card = document.createElement('div');
    const isToday = (idx === 0 || f.dataDate === todayStr);
    card.className = `forecast-card ${isToday ? 'today' : ''}`;

    const { icon, desc } = getWeatherIcon(f.mint, f.maxt, idx);
    const dateFormatted = formatDateShort(f.dataDate);
    const weekday = formatWeekday(f.dataDate);

    card.innerHTML = `
      <div class="today-tag-wrap">
        ${isToday 
          ? '<span class="today-tag-pill">💖 今日天氣</span>' 
          : '<span class="today-tag-pill" style="visibility:hidden; opacity:0;">佔位</span>'}
      </div>
      <div class="fc-date">${dateFormatted}</div>
      <div class="fc-day">${weekday}</div>
      <div class="fc-icon" title="${desc}">${icon}</div>
      <div class="fc-temps">
        <span class="fc-temp-max" title="花花最高溫 (MaxT)">${f.maxt}°</span>
        <span style="color:#CBD5E1; font-weight:bold;">/</span>
        <span class="fc-temp-min" title="泡泡最低溫 (MinT)">${f.mint}°</span>
      </div>
      <div class="fc-desc">${desc}</div>
    `;

    container.appendChild(card);
  });
}

// ============================================================================
// 3. Chart.js Spline Line Chart (The Powerpuff Girls Edition)
// ============================================================================
function renderSplineChart() {
  const canvas = document.getElementById('tempChart');
  if (!canvas) return;

  const forecasts = state.selectedForecasts;
  if (!forecasts || forecasts.length === 0) return;

  const labels = forecasts.map(f => `${formatDateShort(f.dataDate)} (${formatWeekday(f.dataDate)})`);
  const maxTemps = forecasts.map(f => parseFloat(f.maxt));
  const minTemps = forecasts.map(f => parseFloat(f.mint));

  if (state.chartInstance) {
    state.chartInstance.data.labels = labels;
    state.chartInstance.data.datasets[0].data = maxTemps;
    state.chartInstance.data.datasets[1].data = minTemps;
    state.chartInstance.update();
    return;
  }

  const ctx = canvas.getContext('2d');

  // Gradients: Blossom Pink & Bubbles Sky Blue
  const gradientMax = ctx.createLinearGradient(0, 0, 0, 300);
  gradientMax.addColorStop(0, 'rgba(255, 51, 119, 0.28)');
  gradientMax.addColorStop(1, 'rgba(255, 51, 119, 0.00)');

  const gradientMin = ctx.createLinearGradient(0, 0, 0, 300);
  gradientMin.addColorStop(0, 'rgba(0, 180, 216, 0.28)');
  gradientMin.addColorStop(1, 'rgba(0, 180, 216, 0.00)');

  state.chartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: '🌸 花花最高溫 (MaxT)',
          data: maxTemps,
          borderColor: '#FF3377',
          backgroundColor: gradientMax,
          borderWidth: 3.5,
          tension: 0.38,
          fill: true,
          pointBackgroundColor: '#FFFFFF',
          pointBorderColor: '#FF3377',
          pointBorderWidth: 2.5,
          pointRadius: 6,
          pointHoverRadius: 8
        },
        {
          label: '🫧 泡泡最低溫 (MinT)',
          data: minTemps,
          borderColor: '#00B4D8',
          backgroundColor: gradientMin,
          borderWidth: 3.5,
          tension: 0.38,
          fill: true,
          pointBackgroundColor: '#FFFFFF',
          pointBorderColor: '#00B4D8',
          pointBorderWidth: 2.5,
          pointRadius: 6,
          pointHoverRadius: 8
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          display: false
        },
        tooltip: {
          backgroundColor: 'rgba(35, 18, 68, 0.95)',
          titleFont: { family: 'Fredoka', size: 14, weight: 'bold' },
          bodyFont: { family: 'Fredoka', size: 13 },
          padding: 14,
          cornerRadius: 12,
          boxPadding: 6,
          borderColor: '#FF3377',
          borderWidth: 1.5,
          callbacks: {
            label: function(context) {
              return ` ${context.dataset.label}: ${context.parsed.y} °C`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'Fredoka', size: 12, weight: '600' },
            color: '#5B487A'
          }
        },
        y: {
          grid: { color: 'rgba(234, 226, 248, 0.8)' },
          ticks: {
            font: { family: 'Fredoka', size: 12 },
            color: '#5B487A',
            callback: value => `${value}°C`
          }
        }
      }
    }
  });
}

// ============================================================================
// 4. Leaflet Taiwan Weather Map (Fix Issue 2: 徹底移除浮水印)
// ============================================================================
function initMap() {
  const mapElement = document.getElementById('taiwan-map');
  if (!mapElement || state.mapInstance) return;

  // Taiwan Center Coordinates [23.7, 120.95] - 最佳視野
  state.mapInstance = L.map('taiwan-map', {
    center: [23.7, 120.95],
    zoom: 7.7,
    zoomControl: true,
    scrollWheelZoom: true,
    attributionControl: false // 完全移除 Leaflet 預設浮水印文字
  });

  // 使用官方純淨 OpenStreetMap 圖資 (無 Carto "API KEY REQUIRED" 水印)
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 18,
    attribution: '' // 空屬性，配合 CSS 徹底隱藏任何浮水印
  }).addTo(state.mapInstance);

  state.markersLayer = L.layerGroup().addTo(state.mapInstance);

  // 確保全幅大地圖自適應更新尺寸
  setTimeout(() => {
    if (state.mapInstance) state.mapInstance.invalidateSize();
  }, 200);

  window.addEventListener('resize', () => {
    if (state.mapInstance) state.mapInstance.invalidateSize();
  });

}

function getTempColorClass(avg) {
  if (avg < 20) return 'temp-blue';
  if (avg < 25) return 'temp-green';
  if (avg < 30) return 'temp-orange';
  return 'temp-red';
}

function renderMapMarkers() {
  if (!state.mapInstance) initMap();
  if (!state.markersLayer) return;

  state.markersLayer.clearLayers();

  state.mapPoints.forEach(pt => {
    const colorClass = getTempColorClass(pt.avg);
    const isSelected = (pt.regionName === state.currentRegion);

    // Powerpuff Girls Candy Bubble Pin
    const customIcon = L.divIcon({
      className: 'custom-leaflet-icon',
      html: `
        <div class="custom-map-pin ${isSelected ? 'selected' : ''}">
          <div class="pin-bubble ${colorClass}">${pt.label || pt.regionName} ${pt.avg}°</div>
          <div class="pin-pointer"></div>
        </div>
      `,
      iconSize: [64, 32],
      iconAnchor: [32, 30]
    });

    const marker = L.marker([pt.lat, pt.lon], { icon: customIcon });

    const popupContent = `
      <div style="font-family:'Fredoka','Noto Sans TC',sans-serif; min-width:150px; padding:4px;">
        <h4 style="margin:0 0 6px 0; color:#231244; font-weight:800; font-size:1.1rem;">
          💖 ${pt.regionName}
        </h4>
        <div style="font-size:0.88rem; color:#5B487A; margin-bottom:10px; line-height:1.4;">
          氣溫範圍：<strong style="color:#FF3377">${pt.maxt}°C</strong> ~ <strong style="color:#00B4D8">${pt.mint}°C</strong><br>
          即時平均：<strong style="color:#231244;">${pt.avg}°C</strong>
        </div>
        <button onclick="window.selectRegion('${pt.regionName}')" style="background:linear-gradient(135deg, #FF3377 0%, #FF6599 100%); color:#fff; border:2px solid #231244; border-radius:9999px; padding:6px 12px; font-size:0.84rem; font-weight:bold; cursor:pointer; width:100%; box-shadow:2px 2px 0px #231244;">
          🌸 切換觀測此地區 ➔
        </button>
      </div>
    `;

    marker.bindPopup(popupContent);
    marker.on('click', () => {
      selectRegion(pt.regionName);
    });

    state.markersLayer.addLayer(marker);
  });
}

// Global selector helper for popup button
window.selectRegion = function(reg) {
  if (state.currentRegion === reg) return;
  state.currentRegion = reg;
  fetchWeatherData(reg);
};

// ============================================================================
// 5. Forecast Data Table & Search
// ============================================================================
function renderDataTable() {
  const tbody = document.getElementById('table-body');
  if (!tbody) return;

  const searchTerm = (document.getElementById('table-search')?.value || '').toLowerCase().trim();
  tbody.innerHTML = '';

  const filtered = state.selectedForecasts.filter(f => {
    if (!searchTerm) return true;
    return (
      f.regionName.toLowerCase().includes(searchTerm) ||
      f.dataDate.toLowerCase().includes(searchTerm) ||
      String(f.mint).includes(searchTerm) ||
      String(f.maxt).includes(searchTerm)
    );
  });

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; color:#8E7BA8; padding:24px;">查無符合的氣象數據</td></tr>`;
    return;
  }

  filtered.forEach((f, idx) => {
    const mint = parseFloat(f.mint);
    const maxt = parseFloat(f.maxt);
    const avg = ((mint + maxt) / 2).toFixed(1);
    const diff = (maxt - mint).toFixed(1);
    const { icon, desc } = getWeatherIcon(mint, maxt, idx);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><strong>${f.regionName}</strong></td>
      <td>${f.dataDate}</td>
      <td>${formatWeekday(f.dataDate)}</td>
      <td><span class="pill-table pill-table-low">${mint.toFixed(1)} °C</span></td>
      <td><span class="pill-table pill-table-high">${maxt.toFixed(1)} °C</span></td>
      <td><strong>${avg} °C</strong></td>
      <td>${diff} °C</td>
      <td><span style="font-size:1.15rem; margin-right:4px;">${icon}</span> ${desc}</td>
    `;
    tbody.appendChild(tr);
  });
}

// ============================================================================
// 6. Event Listeners & Auto-Sync
// ============================================================================
function setupEventListeners() {
  // Region dropdown change
  document.getElementById('region-select')?.addEventListener('change', (e) => {
    if (e.target.value) {
      selectRegion(e.target.value);
    }
  });

  // Quick pill clicks
  document.getElementById('quick-pills')?.addEventListener('click', (e) => {
    const btn = e.target.closest('.pill-btn');
    if (btn && btn.dataset.region) {
      selectRegion(btn.dataset.region);
    }
  });

  // Table search input
  document.getElementById('table-search')?.addEventListener('input', () => {
    renderDataTable();
  });

  // Manual Sync Button
  document.getElementById('manual-sync-btn')?.addEventListener('click', async () => {
    if (state.isSyncing) return;
    state.isSyncing = true;

    const icon = document.getElementById('sync-icon');
    if (icon) icon.classList.add('spinning');

    showToast('正在與 CWA 氣象署連線同步最新資料...', 'info');
    await fetchWeatherData(state.currentRegion, true);

    state.isSyncing = false;
    if (icon) icon.classList.remove('spinning');
  });

  // Auto-refresh every 5 minutes (300,000 ms)
  state.autoRefreshInterval = setInterval(() => {
    console.log('Powerpuff Girls auto-updating weather...');
    fetchWeatherData(state.currentRegion, false);
  }, 300000);
}

// Initialize on DOM Ready
document.addEventListener('DOMContentLoaded', () => {
  initMap();
  setupEventListeners();
  fetchWeatherData();
});
