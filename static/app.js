/**
 * EVN LAM DONG - BANK REPORT APPLICATION CLIENT-SIDE LOGIC
 * High-performance, modern interactivity, Chart.js visualization
 */

let state = {
    currentMonth: 'Thang 09',
    currentUnit: 'TOÀN CÔNG TY',
    currentCategory: 'ALL',
    metadata: null,
    charts: {}
};

// Utilities
function formatMoney(amount) {
    if (amount === undefined || amount === null) return '0 đ';
    if (amount >= 1e12) return (amount / 1e12).toFixed(2) + ' nghìn tỷ đ';
    if (amount >= 1e9) return (amount / 1e9).toFixed(2) + ' tỷ đ';
    if (amount >= 1e6) return (amount / 1e6).toFixed(2) + ' triệu đ';
    return amount.toLocaleString('vi-VN') + ' đ';
}

function formatNumber(num) {
    if (num === undefined || num === null) return '0';
    return Math.round(num).toLocaleString('vi-VN');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : '⚠️'}</span>
        <span class="toast-msg">${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Live Clock
function updateClock() {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, '0');
    const dStr = `${pad(now.getDate())}/${pad(now.getMonth() + 1)}/${now.getFullYear()} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`;
    const el = document.getElementById('liveClockText');
    if (el) el.textContent = dStr;
}
setInterval(updateClock, 1000);
updateClock();

// Theme Toggle
const btnThemeToggle = document.getElementById('btnThemeToggle');
if (btnThemeToggle) {
    btnThemeToggle.addEventListener('click', () => {
        const isDark = document.body.classList.toggle('theme-dark');
        document.body.classList.toggle('theme-light', !isDark);
        btnThemeToggle.querySelector('.icon-theme').textContent = isDark ? '☀️' : '🌙';
        localStorage.setItem('evn_theme', isDark ? 'dark' : 'light');
        // Update charts theme
        updateAllCharts();
    });

    const savedTheme = localStorage.getItem('evn_theme');
    if (savedTheme === 'dark') {
        document.body.classList.remove('theme-light');
        document.body.classList.add('theme-dark');
        btnThemeToggle.querySelector('.icon-theme').textContent = '☀️';
    }
}

// Tab Switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
        btn.classList.add('active');
        const targetId = btn.getAttribute('data-tab');
        const targetPane = document.getElementById(targetId);
        if (targetPane) targetPane.classList.add('active');

        if (targetId === 'tab-overview') {
            setTimeout(updateAllCharts, 100);
        }
    });
});

// App Initialization
async function initApp() {
    try {
        await loadMetadata();
        await refreshAllData();
    } catch (err) {
        console.error('Initialization error:', err);
        showToast('Lỗi tải dữ liệu ban đầu: ' + err.message, 'error');
    }
}

// Load Metadata
async function loadMetadata() {
    const res = await fetch('/api/metadata');
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    state.metadata = json;

    // Populate Months Dropdown
    const selectMonth = document.getElementById('selectMonth');
    if (selectMonth && json.available_months.length > 0) {
        selectMonth.innerHTML = '';
        json.available_months.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m;
            opt.textContent = m === 'Lũy kế 9 tháng' ? 'Lũy kế 9 tháng 2026' : `${m}/2026`;
            selectMonth.appendChild(opt);
        });
        selectMonth.value = state.currentMonth;
    }

    // Populate Units Dropdown
    const selectUnit = document.getElementById('selectUnit');
    if (selectUnit && json.units.length > 0) {
        selectUnit.innerHTML = '<option value="TOÀN CÔNG TY">Toàn Công ty (12 Điện lực)</option>';
        json.units.forEach(u => {
            const opt = document.createElement('option');
            opt.value = u;
            opt.textContent = `Điện lực ${u}`;
            selectUnit.appendChild(opt);
        });
        selectUnit.value = state.currentUnit;
    }
}

// Global Refresh Data
async function refreshAllData() {
    await Promise.all([
        loadOverview(),
        loadRankings(),
        loadBanks(),
        loadAnalysis(),
        loadTrends()
    ]);
}

// 1. Overview KPIs
async function loadOverview() {
    const res = await fetch(`/api/overview?month=${encodeURIComponent(state.currentMonth)}&unit=${encodeURIComponent(state.currentUnit)}`);
    const json = await res.json();
    if (!json.success) return;

    const ov = json.data;

    // KPI 1: Revenue
    document.getElementById('kpiRevenue').textContent = formatMoney(ov.total_st);
    document.getElementById('kpiRevenueSub').textContent = `Chi tiết tại: ${state.currentUnit}`;
    const momEl = document.getElementById('kpiRevenueMom');
    if (ov.mom) {
        const growSt = ov.mom.growth_st_pct;
        const isPos = growSt >= 0;
        momEl.innerHTML = `
            <span class="badge-growth ${isPos ? 'positive' : 'negative'}">${isPos ? '+' : ''}${growSt.toFixed(2)}%</span>
            <span class="growth-label">so với ${ov.mom.prev_month} (${isPos ? '+' : ''}${formatMoney(ov.mom.diff_st)})</span>
        `;
    } else {
        momEl.innerHTML = `<span class="growth-label text-muted">Dữ liệu kỳ lũy kế / chưa có đối chiếu</span>`;
    }

    // KPI 2: Invoices
    document.getElementById('kpiInvoices').textContent = formatNumber(ov.total_hd) + ' HĐ';
    const momHdEl = document.getElementById('kpiInvoicesMom');
    if (ov.mom) {
        const growHd = ov.mom.growth_hd_pct;
        const isPos = growHd >= 0;
        momHdEl.innerHTML = `
            <span class="badge-growth ${isPos ? 'positive' : 'negative'}">${isPos ? '+' : ''}${growHd.toFixed(2)}%</span>
            <span class="growth-label">so với ${ov.mom.prev_month}</span>
        `;
    } else {
        momHdEl.innerHTML = `<span class="growth-label text-muted">Tổng số giao dịch thành công</span>`;
    }

    // KPI 3: Digital Ratio
    document.getElementById('kpiDigitalRatio').textContent = ov.digital_ratio_hd.toFixed(1) + '%';
    const appCh = ov.channels.find(c => c.id === 'app_vi') || { hd: 0, st: 0 };
    document.getElementById('kpiDigitalValue').textContent = `${formatNumber(appCh.hd)} HĐ • ${formatMoney(appCh.st)}`;
    document.getElementById('kpiDigitalBar').style.width = Math.min(100, ov.digital_ratio_hd) + '%';

    // KPI 4: UNC
    const uncCh = ov.channels.find(c => c.id === 'unc') || { hd: 0, st: 0, pct_st: 0 };
    document.getElementById('kpiUncRatio').textContent = uncCh.pct_st.toFixed(1) + '%';
    document.getElementById('kpiUncValue').textContent = `${formatNumber(uncCh.hd)} HĐ • ${formatMoney(uncCh.st)}`;
    const uncBar = document.getElementById('kpiUncBar');
    if (uncBar) uncBar.style.width = Math.min(100, uncCh.pct_st) + '%';

    // Donut Center Text
    const dcVal = document.getElementById('donutCenterVal');
    if (dcVal) dcVal.textContent = ov.digital_ratio_hd.toFixed(1) + '%';

    // Render Channels Doughnut Chart
    renderChannelsChart(ov.channels);
}

// 2. Rankings (12 Điện Lực)
async function loadRankings() {
    const res = await fetch(`/api/rankings?month=${encodeURIComponent(state.currentMonth)}`);
    const json = await res.json();
    if (!json.success) return;

    const ranks = json.data;
    const tbody = document.getElementById('tbodyUnitsMatrix');
    const tfoot = document.getElementById('tfootUnitsMatrix');
    tbody.innerHTML = '';

    let sumAppHd = 0, sumAppSt = 0, sumUncHd = 0, sumUncSt = 0, sumHd = 0, sumSt = 0;

    ranks.forEach((u, idx) => {
        sumAppHd += u.hd_app;
        sumAppSt += u.st_app;
        sumUncHd += u.hd_unc;
        sumUncSt += u.st_unc;
        sumHd += u.hd_tong;
        sumSt += u.st_tong;

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${idx}</strong></td>
            <td><strong>Điện lực ${u.unit}</strong></td>
            <td class="text-right font-mono">${formatNumber(u.hd_app)}</td>
            <td class="text-right font-mono">${formatNumber(u.st_app)}</td>
            <td class="text-right font-mono">${formatNumber(u.hd_unc)}</td>
            <td class="text-right font-mono">${formatNumber(u.st_unc)}</td>
            <td class="text-right font-mono font-bold">${formatNumber(u.hd_tong)}</td>
            <td class="text-right font-mono font-bold text-primary">${formatNumber(u.st_tong)}</td>
            <td class="text-right font-bold text-emerald">${u.pct_digital_hd.toFixed(1)}%</td>
            <td>
                <button class="btn btn-outline" style="padding: 3px 8px; font-size: 11px;" onclick="drillDownUnit('${u.unit}')">
                    Chi tiết
                </button>
            </td>
        `;
        tbody.appendChild(tr);
    });

    // Foot row
    const avgDig = sumHd > 0 ? (sumAppHd / sumHd * 100) : 0;
    tfoot.innerHTML = `
        <tr>
            <td colspan="2">TỔNG TOÀN CÔNG TY</td>
            <td class="text-right font-mono font-bold">${formatNumber(sumAppHd)}</td>
            <td class="text-right font-mono font-bold">${formatNumber(sumAppSt)}</td>
            <td class="text-right font-mono font-bold">${formatNumber(sumUncHd)}</td>
            <td class="text-right font-mono font-bold">${formatNumber(sumUncSt)}</td>
            <td class="text-right font-mono font-bold">${formatNumber(sumHd)}</td>
            <td class="text-right font-mono font-bold text-primary">${formatNumber(sumSt)}</td>
            <td class="text-right font-bold text-emerald">${avgDig.toFixed(1)}%</td>
            <td>-</td>
        </tr>
    `;

    renderUnitsRankingChart(ranks);
}

// 3. Banks Matrix
async function loadBanks() {
    const res = await fetch(`/api/banks?month=${encodeURIComponent(state.currentMonth)}&unit=${encodeURIComponent(state.currentUnit)}`);
    const json = await res.json();
    if (!json.success) return;

    const data = json.data;
    let banks = data.banks;

    // Filter by category
    if (state.currentCategory !== 'ALL') {
        banks = banks.filter(b => b.category === state.currentCategory);
    }

    const tbody = document.getElementById('tbodyBanksMatrix');
    const tfoot = document.getElementById('tfootBanksMatrix');
    tbody.innerHTML = '';

    let sumHd = 0, sumSt = 0;

    banks.forEach((b, idx) => {
        sumHd += b.hd_tong;
        sumSt += b.st_tong;

        let badgeClass = 'bg-blue-subtle text-primary';
        if (b.category.includes('Big 4')) badgeClass = 'bg-emerald-subtle text-emerald';
        if (b.category.includes('Ví')) badgeClass = 'bg-purple-subtle';

        const mainChannel = b.st_unc > b.st_app ? 'UNC Doanh nghiệp' : 'App / Ví / Tự động';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${idx}</strong></td>
            <td>
                <strong>${b.bank_short}</strong>
                <div style="font-size: 11px; color: var(--text-muted);">${b.bank_name}</div>
            </td>
            <td><span class="badge-tag ${badgeClass}" style="font-size: 10px;">${b.category}</span></td>
            <td class="text-right font-mono">${formatNumber(b.hd_tong)}</td>
            <td class="text-right font-mono">${b.share_hd.toFixed(2)}%</td>
            <td class="text-right font-mono font-bold">${formatNumber(b.st_tong)}</td>
            <td class="text-right font-mono font-bold text-primary">${b.share_st.toFixed(2)}%</td>
            <td class="text-right"><span style="font-size: 11.5px;">${mainChannel}</span></td>
        `;
        tbody.appendChild(tr);
    });

    tfoot.innerHTML = `
        <tr>
            <td colspan="3">TỔNG CỘNG</td>
            <td class="text-right font-mono font-bold">${formatNumber(sumHd)}</td>
            <td class="text-right font-mono font-bold">100.00%</td>
            <td class="text-right font-mono font-bold text-primary">${formatNumber(sumSt)}</td>
            <td class="text-right font-mono font-bold">100.00%</td>
            <td>-</td>
        </tr>
    `;

    renderBanksShareChart(data.banks);
}

// 4. Analysis Document View
async function loadAnalysis() {
    const res = await fetch(`/api/analysis?month=${encodeURIComponent(state.currentMonth)}`);
    const json = await res.json();
    if (!json.success) return;

    const rep = json.data;

    document.getElementById('docMainTitle').textContent = rep.title;
    document.getElementById('docPeriodSubtitle').textContent = `Kỳ báo cáo: ${state.currentMonth}/2026`;
    document.getElementById('docExecutiveSummary').textContent = rep.executive_summary;
    document.getElementById('docChannelAnalysis').textContent = rep.channel_analysis;
    document.getElementById('docUnitAnalysis').textContent = rep.unit_analysis;
    document.getElementById('docBankAnalysis').textContent = rep.bank_analysis;

    const recUl = document.getElementById('docRecommendations');
    recUl.innerHTML = '';
    rep.recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recUl.appendChild(li);
    });
}

// 5. Trends Timeline
async function loadTrends() {
    const res = await fetch(`/api/trends?unit=${encodeURIComponent(state.currentUnit)}`);
    const json = await res.json();
    if (!json.success) return;

    renderTrendsChart(json.data);
}

// =====================================================================
// Chart.js Visualizations
// =====================================================================

function getChartColors() {
    const isDark = document.body.classList.contains('theme-dark');
    return {
        textColor: isDark ? '#94a3b8' : '#475569',
        gridColor: isDark ? '#24344d' : '#e2e8f0',
        cardBg: isDark ? '#131d31' : '#ffffff'
    };
}

// Chart 1: Channels Doughnut
function renderChannelsChart(channels) {
    const ctx = document.getElementById('chartChannels');
    if (!ctx) return;

    if (state.charts.channels) state.charts.channels.destroy();

    const labels = channels.map(c => c.name);
    const dataSt = channels.map(c => c.st);
    const colors = ['#003B7A', '#10b981', '#f59e0b', '#8b5cf6'];

    state.charts.channels = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: dataSt,
                backgroundColor: colors,
                borderWidth: 3,
                borderColor: document.body.classList.contains('theme-dark') ? '#131d31' : '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '72%',
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((val / total) * 100).toFixed(1);
                            return ` ${context.label}: ${formatMoney(val)} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });

    // Render custom legend with rich cards and progress bars
    const legEl = document.getElementById('channelsLegend');
    if (legEl) {
        legEl.innerHTML = '';
        channels.forEach((c, idx) => {
            const item = document.createElement('div');
            item.className = 'legend-item';
            item.innerHTML = `
                <div class="legend-header-line">
                    <div class="legend-left">
                        <span class="legend-dot" style="background: ${colors[idx]}"></span>
                        <span class="legend-name">${c.name}</span>
                    </div>
                    <span class="legend-amt">${formatMoney(c.st)}</span>
                </div>
                <div class="legend-sub-line">
                    <span class="legend-chip chip-money">${c.pct_st.toFixed(1)}% Tiền</span>
                    <span class="legend-chip chip-invoice">${c.pct_hd.toFixed(1)}% HĐ (${formatNumber(c.hd)})</span>
                </div>
                <div class="legend-track">
                    <div class="legend-fill" style="width: ${Math.min(100, c.pct_st)}%; background: ${colors[idx]}"></div>
                </div>
            `;
            legEl.appendChild(item);
        });
    }
}

// Chart 2: 9-Month Trends (Line & Bar)
function renderTrendsChart(timeline) {
    const ctx = document.getElementById('chartTrends');
    if (!ctx) return;

    if (state.charts.trends) state.charts.trends.destroy();

    const cfg = getChartColors();
    const labels = timeline.map(t => t.month.replace('Thang ', 'T'));
    const dataSt = timeline.map(t => +(t.st_tong / 1e9).toFixed(2)); // Doanh thu Tỷ VNĐ
    const dataHd = timeline.map(t => t.hd_tong); // Số lượng HĐ

    state.charts.trends = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Doanh thu (Tỷ VNĐ)',
                    data: dataSt,
                    type: 'bar',
                    backgroundColor: 'rgba(0, 59, 122, 0.85)',
                    hoverBackgroundColor: '#0056b3',
                    borderRadius: 6,
                    yAxisID: 'y',
                    order: 2,
                    barPercentage: 0.55
                },
                {
                    label: 'Số lượng HĐ',
                    data: dataHd,
                    type: 'line',
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.12)',
                    borderWidth: 3,
                    fill: false,
                    tension: 0.35,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#ffffff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 7,
                    yAxisID: 'y1',
                    order: 1
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
            scales: {
                x: {
                    grid: { display: false },
                    ticks: { color: cfg.textColor, font: { weight: 600 } }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    grid: { color: cfg.gridColor },
                    ticks: {
                        color: cfg.textColor,
                        callback: v => v + ' tỷ'
                    },
                    title: {
                        display: true,
                        text: 'Doanh thu (Tỷ VNĐ)',
                        color: cfg.textColor,
                        font: { size: 11, weight: 600 }
                    }
                },
                y1: {
                    type: 'linear',
                    position: 'right',
                    grid: { display: false },
                    ticks: {
                        color: cfg.textColor,
                        callback: v => (v / 1000).toFixed(0) + 'k'
                    },
                    title: {
                        display: true,
                        text: 'Số lượng HĐ',
                        color: cfg.textColor,
                        font: { size: 11, weight: 600 }
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: cfg.textColor,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: { weight: 600, size: 12 },
                        padding: 16
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    titleFont: { size: 13, weight: 700 },
                    bodyFont: { size: 12 },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(ctx) {
                            if (ctx.dataset.type === 'line') {
                                return ` Số lượng HĐ: ${formatNumber(ctx.raw)} HĐ`;
                            } else {
                                return ` Doanh thu: ${ctx.raw} tỷ VNĐ`;
                            }
                        }
                    }
                }
            }
        }
    });
}

// Chart 3: Units Ranking (Horizontal Bar)
function renderUnitsRankingChart(ranks) {
    const ctx = document.getElementById('chartUnitsRanking');
    if (!ctx) return;

    if (state.charts.ranking) state.charts.ranking.destroy();

    const cfg = getChartColors();
    const sorted = [...ranks].reverse(); // reverse for horizontal bar top at top
    const labels = sorted.map(u => u.unit);
    const dataSt = sorted.map(u => +(u.st_tong / 1e9).toFixed(2));

    const totalCount = sorted.length;
    const barColors = sorted.map((u, i) => {
        const rank = totalCount - i;
        if (rank === 1) return '#f59e0b'; // Gold for #1
        if (rank === 2) return '#0056b3'; // Deep Navy for #2
        if (rank === 3) return '#10b981'; // Emerald for #3
        return 'rgba(0, 59, 122, 0.65)'; // Corporate Navy for rest
    });

    state.charts.ranking = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Doanh thu (Tỷ VNĐ)',
                data: dataSt,
                backgroundColor: barColors,
                borderRadius: 5,
                barPercentage: 0.7
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    grid: { color: cfg.gridColor },
                    ticks: { color: cfg.textColor, callback: v => v + ' tỷ' }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: cfg.textColor, font: { weight: 600, size: 11.5 } }
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: ctx => ` Doanh thu: ${ctx.raw} tỷ VNĐ`
                    }
                }
            }
        }
    });
}

// Chart 4: Banks Share (Top 6 + Others)
function renderBanksShareChart(banks) {
    const ctx = document.getElementById('chartBanksShare');
    if (!ctx) return;

    if (state.charts.banksShare) state.charts.banksShare.destroy();

    const cfg = getChartColors();
    const top6 = banks.slice(0, 6);
    const othersSt = banks.slice(6).reduce((acc, b) => acc + b.st_tong, 0);

    const labels = [...top6.map(b => b.bank_short), 'Các đối tác khác'];
    const dataSt = [...top6.map(b => b.st_tong), othersSt];
    const colors = ['#003B7A', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ec4899', '#94a3b8'];

    state.charts.banksShare = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: dataSt,
                backgroundColor: colors,
                borderWidth: 2,
                borderColor: document.body.classList.contains('theme-dark') ? '#131d31' : '#ffffff',
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '58%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        color: cfg.textColor,
                        font: { size: 11.5, weight: 600 },
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.92)',
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(ctx) {
                            const val = ctx.raw;
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((val / total) * 100).toFixed(1);
                            return ` ${ctx.label}: ${formatMoney(val)} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
}

function updateAllCharts() {
    loadOverview();
    loadRankings();
    loadBanks();
    loadTrends();
}

// =====================================================================
// Event Handlers & Drill-down
// =====================================================================

document.getElementById('selectMonth').addEventListener('change', (e) => {
    state.currentMonth = e.target.value;
    refreshAllData();
    showToast(`Đã chuyển kỳ dữ liệu sang ${state.currentMonth}`, 'success');
});

document.getElementById('selectUnit').addEventListener('change', (e) => {
    state.currentUnit = e.target.value;
    loadOverview();
    loadBanks();
    loadTrends();
    showToast(`Đã lọc dữ liệu theo: ${state.currentUnit}`, 'success');
});

document.getElementById('selectCategory').addEventListener('change', (e) => {
    state.currentCategory = e.target.value;
    loadBanks();
});

// Search filter for Units Table
document.getElementById('searchUnitTable').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('#tbodyUnitsMatrix tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
    });
});

// Search filter for Banks Table
document.getElementById('searchBankTable').addEventListener('input', (e) => {
    const q = e.target.value.toLowerCase();
    document.querySelectorAll('#tbodyBanksMatrix tr').forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(q) ? '' : 'none';
    });
});

// Drill-down function
window.drillDownUnit = function(unitName) {
    state.currentUnit = unitName;
    document.getElementById('selectUnit').value = unitName;
    loadOverview();
    loadBanks();
    loadTrends();
    document.querySelector('[data-tab="tab-overview"]').click();
    showToast(`Đang xem chi tiết Điện lực ${unitName}`, 'success');
};

// Export Handlers
document.getElementById('btnExportDocx').addEventListener('click', () => {
    window.location.href = `/api/export/docx?month=${encodeURIComponent(state.currentMonth)}`;
    showToast('Đang tải xuống báo cáo thuyết minh Word (.docx)...', 'success');
});

document.getElementById('btnExportExcel').addEventListener('click', () => {
    window.location.href = `/api/export/excel?month=${encodeURIComponent(state.currentMonth)}`;
    showToast('Đang tải xuống bảng tổng hợp Excel (.xlsx)...', 'success');
});

document.getElementById('btnPrintReport').addEventListener('click', () => {
    // Switch to analysis tab before printing
    document.querySelector('[data-tab="tab-analysis"]').click();
    setTimeout(() => window.print(), 300);
});

// Reload Data
document.getElementById('btnReloadData').addEventListener('click', async () => {
    showToast('Đang quét và làm mới lại dữ liệu từ Excel...', 'success');
    const res = await fetch('/api/reload', { method: 'POST' });
    const json = await res.json();
    if (json.success) {
        await initApp();
        showToast(json.message, 'success');
    } else {
        showToast('Lỗi: ' + json.error, 'error');
    }
});

document.getElementById('btnFlushCache').addEventListener('click', async () => {
    document.getElementById('btnReloadData').click();
});

// =====================================================================
// Upload Modal & Drag-and-drop
// =====================================================================

const uploadModal = document.getElementById('uploadModal');
const btnOpenUploadModal = document.getElementById('btnOpenUploadModal');
const btnCloseUploadModal = document.getElementById('btnCloseUploadModal');
const btnCancelModal = document.getElementById('btnCancelModal');
let selectedFile = null;

if (btnOpenUploadModal) {
    btnOpenUploadModal.addEventListener('click', () => {
        uploadModal.style.display = 'flex';
    });
}

[btnCloseUploadModal, btnCancelModal].forEach(el => {
    if (el) el.addEventListener('click', () => {
        uploadModal.style.display = 'none';
    });
});

// Setup Dropzones
function setupDropZone(dropZoneId, fileInputId, infoElId) {
    const dropZone = document.getElementById(dropZoneId);
    const fileInput = document.getElementById(fileInputId);
    if (!dropZone || !fileInput) return;

    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelect(e.dataTransfer.files[0], infoElId);
        }
    });

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileSelect(fileInput.files[0], infoElId);
        }
    });
}

function handleFileSelect(file, infoElId) {
    selectedFile = file;
    const infoEl = document.getElementById(infoElId);
    if (infoEl) {
        infoEl.style.display = 'block';
        infoEl.innerHTML = `<strong>Đã chọn file:</strong> ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    }
    showToast(`Đã chọn file: ${file.name}`, 'success');
}

setupDropZone('modalDropZone', 'modalFileInput', 'modalFileInfo');
setupDropZone('dropZone', 'fileInput', 'uploadStatusBox');

// Upload Submit
document.getElementById('btnConfirmUpload').addEventListener('click', async () => {
    if (!selectedFile) {
        showToast('Vui lòng chọn file Excel trước khi nạp!', 'error');
        return;
    }

    const monthLabel = document.getElementById('modalMonthInput').value;
    await doUpload(selectedFile, monthLabel);
    uploadModal.style.display = 'none';
});

document.getElementById('btnUploadSubmit').addEventListener('click', async () => {
    if (!selectedFile) {
        showToast('Vui lòng chọn file Excel trước khi nạp!', 'error');
        return;
    }
    const monthLabel = document.getElementById('inputMonthLabel').value;
    await doUpload(selectedFile, monthLabel);
});

async function doUpload(file, monthLabel) {
    const formData = new FormData();
    formData.append('file', file);
    if (monthLabel) formData.append('month_label', monthLabel);

    showToast('Đang xử lý nạp file và cập nhật dữ liệu...', 'success');

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        const json = await res.json();
        if (json.success) {
            showToast(json.message, 'success');
            await initApp();
            if (json.month) {
                state.currentMonth = json.month;
                document.getElementById('selectMonth').value = json.month;
                await refreshAllData();
            }
        } else {
            showToast('Lỗi: ' + json.error, 'error');
        }
    } catch (err) {
        showToast('Lỗi khi nạp file: ' + err.message, 'error');
    }
}

// Start app
document.addEventListener('DOMContentLoaded', initApp);
