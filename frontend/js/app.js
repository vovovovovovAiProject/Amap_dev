/**
 * 主应用逻辑 - 标签页版本
 */

// 全局变量
let mapManager = null;
let timelineRenderer = null;
let tripData = null;
let currentDayIndex = 0;
let currentTab = 'chat';

/**
 * 初始化应用
 */
function initApp() {
    // 初始化标签页
    initTabs();

    // 初始化地图（延迟到切换到地图标签时）
    // mapManager 会在第一次切换到地图标签时初始化

    // 初始化时间轴渲染器
    timelineRenderer = new TimelineRenderer('timeline');

    // 绑定事件
    bindEvents();

    // 检查URL参数
    const urlParams = new URLSearchParams(window.location.search);
    const tripId = urlParams.get('trip_id');
    if (tripId) {
        loadTripDetail(tripId);
    }

    console.log('智途无忧 应用初始化完成');
}

/**
 * 初始化标签页
 */
function initTabs() {
    const tabButtons = document.querySelectorAll('.tab-btn');

    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            switchTab(tabName);
        });
    });
}

/**
 * 切换标签页
 */
function switchTab(tabName) {
    currentTab = tabName;

    // 更新标签按钮状态
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });

    // 更新标签内容显示
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tabName}`);
    });

    // 特殊处理
    if (tabName === 'map') {
        // 延迟初始化地图
        if (!mapManager) {
            try {
                mapManager = new MapManager('mapView');
                mapManager.init();
                console.log('地图初始化成功');
            } catch (e) {
                console.error('地图初始化失败:', e);
            }
        }

        // 如果有行程数据，刷新地图显示
        if (tripData) {
            setTimeout(() => {
                switchDay(currentDayIndex);
            }, 100);
        }
    } else if (tabName === 'trips') {
        // 加载行程列表
        loadTripsList();
    }
}

/**
 * 绑定事件
 */
function bindEvents() {
    // 保存按钮
    const saveTripBtn = document.getElementById('saveTripBtn');
    if (saveTripBtn) {
        saveTripBtn.addEventListener('click', handleSaveTrip);
    }

    // 打开高德地图按钮
    const openAmapBtn = document.getElementById('openAmapBtn');
    if (openAmapBtn) {
        openAmapBtn.addEventListener('click', openInAmap);
    }

    // 分享按钮
    const shareBtn = document.getElementById('shareBtn');
    if (shareBtn) {
        shareBtn.addEventListener('click', handleShare);
    }

    // 地图控制按钮
    const toggle3DBtn = document.getElementById('toggle3DBtn');
    if (toggle3DBtn) {
        toggle3DBtn.addEventListener('click', () => {
            if (mapManager) {
                const is3D = mapManager.toggle3DMode();
                toggle3DBtn.classList.toggle('active-3d', is3D);
            }
        });
    }

    // 实时路况切换按钮
    const toggleTrafficBtn = document.getElementById('toggleTrafficBtn');
    if (toggleTrafficBtn) {
        toggleTrafficBtn.addEventListener('click', () => {
            if (mapManager) {
                const isTrafficVisible = mapManager.toggleTraffic();
                toggleTrafficBtn.classList.toggle('active-traffic', isTrafficVisible);
            }
        });
    }

    const zoomInBtn = document.getElementById('zoomInBtn');
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', () => {
            if (mapManager) mapManager.zoomIn();
        });
    }

    const zoomOutBtn = document.getElementById('zoomOutBtn');
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', () => {
            if (mapManager) mapManager.zoomOut();
        });
    }
}

/**
 * 更新行程显示（供 chat.js 调用）
 */
function updateTripDisplay(data) {
    tripData = data;
    currentDayIndex = 0;

    // 规范化数据
    normalizeTripData(tripData);

    // 显示行程结果
    displayTrip(tripData);

    // 隐藏无行程提示
    const noTripHint = document.getElementById('noTripHint');
    if (noTripHint) {
        noTripHint.classList.add('hidden');
    }
}

/**
 * 加载行程详情
 */
async function loadTripDetail(id) {
    try {
        const response = await api.getTripDetail(id);
        if (response.success && response.data) {
            tripData = response.data;
            normalizeTripData(tripData);
            displayTrip(tripData);

            // 切换到地图标签
            switchTab('map');

            // 只更新对话管理器的当前行程状态，不添加消息
            if (chatManager) {
                chatManager.currentTrip = tripData;
            }
        } else {
            alert('获取行程详情失败: ' + (response.message || '未知错误'));
        }
    } catch (error) {
        console.error('Failed to load trip:', error);
        alert('无法加载行程，请稍后重试');
    }
}

/**
 * 规范化行程数据结构
 */
function normalizeTripData(data) {
    if (!data.days && data.pois) {
        data.days = [{
            day_index: 1,
            items: data.pois.map((poi, index) => ({
                ...poi,
                order: index
            }))
        }];
    }

    if (!data.trip && data.title) {
        data.trip = {
            title: data.title,
            city: data.city || '未知城市',
            days: data.days.length,
            summary: data.summary
        };
    }
}

/**
 * 显示行程结果
 */
function displayTrip(data) {
    const tripInfo = data.trip || data;
    const tripResult = document.getElementById('tripResult');
    const noTripHint = document.getElementById('noTripHint');

    // 隐藏无行程提示，显示行程结果
    if (noTripHint) noTripHint.classList.add('hidden');
    if (tripResult) tripResult.classList.remove('hidden');

    // 更新标题和摘要
    document.getElementById('tripTitle').textContent = tripInfo.title;
    document.getElementById('tripSummaryText').textContent = tripInfo.summary || '行程已生成，请查看下方详情。';

    // 更新天气
    if (data.weather && data.weather.casts && data.weather.casts.length > 0) {
        const today = data.weather.casts[0];
        const weatherIcon = getWeatherIcon(today.dayweather);
        document.getElementById('weatherCard').innerHTML = `
            <span class="weather-icon">${weatherIcon}</span>
            <span class="weather-text">${today.dayweather} ${today.daytemp}°C</span>
        `;
    }

    // 更新 AI 旅行智囊
    const aiInsightsPanel = document.getElementById('aiInsights');
    if (data.insights && aiInsightsPanel) {
        renderAIInsights(data.insights);
        aiInsightsPanel.classList.remove('hidden');
    } else if (aiInsightsPanel) {
        aiInsightsPanel.classList.add('hidden');
    }

    // 更新统计数据
    updateStats(data);

    // 渲染天数标签
    renderDayTabs(data.days);

    // 默认展示第一天
    if (data.days && data.days.length > 0) {
        switchDay(0);
    }
}

/**
 * 渲染 AI 智囊建议
 */
function renderAIInsights(insights) {
    const packingList = document.getElementById('packingList');
    const delicaciesList = document.getElementById('delicaciesList');
    const proTipsList = document.getElementById('proTipsList');

    if (packingList && insights.packing_list) {
        packingList.innerHTML = insights.packing_list.map(item => `<li>${item}</li>`).join('');
    }
    if (delicaciesList && insights.local_delicacies) {
        delicaciesList.innerHTML = insights.local_delicacies.map(item => `<li>${item}</li>`).join('');
    }
    if (proTipsList && insights.pro_tips) {
        proTipsList.innerHTML = insights.pro_tips.map(item => `<li>${item}</li>`).join('');
    }
}

/**
 * 更新统计信息
 */
function updateStats(data) {
    let totalDuration = 0;  // 分钟
    let totalDistance = 0;  // 米
    let totalCost = 0;      // 元

    if (data.days) {
        data.days.forEach(day => {
            if (day.items) {
                day.items.forEach(item => {
                    // 只累加有效的游览时长（酒店的visit_duration为0，不应该默认60）
                    const duration = item.visit_duration;
                    if (duration !== undefined && duration !== null) {
                        totalDuration += duration;
                    }
                    totalCost += (item.cost || 0);
                });
            }
            if (day.routes) {
                day.routes.forEach(route => {
                    totalDistance += (route.distance || 0);  // 米
                    // route.duration 是秒，需要转换为分钟
                    totalDuration += Math.round((route.duration || 0) / 60);
                });
            }
        });
    }

    document.getElementById('totalDuration').textContent = Math.round(totalDuration / 60);  // 转换为小时
    document.getElementById('totalDistance').textContent = (totalDistance / 1000).toFixed(1);  // 转换为公里
    document.getElementById('totalCost').textContent = Math.round(totalCost);
}

/**
 * 渲染��数标签
 */
function renderDayTabs(days) {
    const wrapper = document.getElementById('dayTabsWrapper');
    const container = document.getElementById('dayTabs');

    if (!days || days.length <= 1) {
        wrapper.classList.add('hidden');
        return;
    }

    wrapper.classList.remove('hidden');
    container.innerHTML = days.map((day, index) => `
        <button class="day-tab ${index === 0 ? 'active' : ''}" data-day="${index}">
            Day ${day.day_index}
        </button>
    `).join('');

    container.querySelectorAll('.day-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const dayIndex = parseInt(tab.dataset.day);
            switchDay(dayIndex);
        });
    });
}

/**
 * 切换天数
 */
function switchDay(dayIndex) {
    currentDayIndex = dayIndex;

    // 更新标签状态
    document.querySelectorAll('.day-tab').forEach((tab, index) => {
        tab.classList.toggle('active', index === dayIndex);
    });

    // 获取当天数据
    const currentDay = tripData.days[dayIndex];
    if (!currentDay) return;

    // 更新每日摘要
    const daySummary = document.getElementById('daySummary');
    if (currentDay.summary) {
        daySummary.textContent = currentDay.summary;
        daySummary.classList.remove('hidden');
    } else {
        daySummary.classList.add('hidden');
    }

    // 渲染时间轴
    const dayPois = currentDay.items || [];
    if (timelineRenderer) {
        timelineRenderer.render({ pois: dayPois, routes: currentDay.routes || [] });
    }

    // 更新地图
    if (mapManager) {
        const dayViewData = {
            pois: dayPois,
            routes: currentDay.routes || []
        };
        mapManager.showTrip(dayViewData);
    }

    // 保存当前POIs供其他功能使用
    tripData.pois = dayPois;
}

/**
 * 获取天气图标
 */
function getWeatherIcon(weather) {
    const iconMap = {
        '晴': '☀️', '多云': '⛅', '阴': '☁️',
        '小雨': '🌧️', '中雨': '🌧️', '大雨': '⛈️',
        '雪': '❄️', '雾': '🌫️'
    };
    return iconMap[weather] || '🌤️';
}

/**
 * 保存行程
 */
async function handleSaveTrip() {
    if (!tripData) return;

    const btn = document.getElementById('saveTripBtn');
    const originalText = btn.innerHTML;
    btn.textContent = '保存中...';
    btn.disabled = true;

    try {
        const saveData = {
            ...tripData.trip,
            trip_days: tripData.days.map(day => ({
                day_index: day.day_index,
                date: day.date || null,
                summary: day.summary || null,
                items: day.items.map(item => ({
                    poi_id: item.poi_id || null,
                    name: item.name,
                    location: item.location,
                    address: item.address || null,
                    type: item.type || null,
                    order: item.order,
                    visit_duration: item.visit_duration || 60,
                    cost: item.cost || 0,
                    photos: item.photos || []
                })),
                routes: day.routes || []
            }))
        };

        await api.saveTrip(saveData);
        alert('行程保存成功！');

        // 刷新行程列表
        if (currentTab === 'trips') {
            loadTripsList();
        }
    } catch (error) {
        console.error('保存失败:', error);
        alert('保存失败，请重试');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/**
 * 在高德地图中打开
 */
function openInAmap() {
    if (!tripData || !tripData.pois || tripData.pois.length === 0) return;

    const firstPoi = tripData.pois[0];
    const [lng, lat] = firstPoi.location.split(',');
    const url = `https://uri.amap.com/marker?position=${lng},${lat}&name=${encodeURIComponent(firstPoi.name)}`;
    window.open(url, '_blank');
}

/**
 * 分享行程
 */
function handleShare() {
    if (navigator.share) {
        navigator.share({
            title: tripData?.trip?.title || '我的行程',
            text: '来看看我用智途无忧规划的行程！',
            url: window.location.href
        });
    } else {
        // 复制链接
        navigator.clipboard.writeText(window.location.href);
        alert('链接已复制到剪贴板');
    }
}

/**
 * 加载行程列表
 */
async function loadTripsList() {
    const grid = document.getElementById('tripGrid');
    if (!grid) return;

    grid.innerHTML = '<div class="loading-spinner" style="margin: 40px auto;"></div>';

    try {
        const trips = await api.listTrips();
        grid.innerHTML = '';

        if (!trips || trips.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <h3>暂无行程</h3>
                    <p>在"对话"标签页中告诉我你的旅行计划</p>
                    <button class="go-chat-btn" onclick="switchTab('chat')">开始对话</button>
                </div>
            `;
            return;
        }

        trips.forEach(trip => {
            const card = document.createElement('div');
            card.className = 'trip-card';

            // 格式化保存时间
            let timeStr = '';
            if (trip.created_at) {
                const date = new Date(trip.created_at);
                const now = new Date();
                const diffMs = now - date;
                const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

                if (diffDays === 0) {
                    // 今天
                    timeStr = `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
                } else if (diffDays === 1) {
                    timeStr = '昨天';
                } else if (diffDays < 7) {
                    timeStr = `${diffDays}天前`;
                } else {
                    timeStr = `${date.getMonth() + 1}月${date.getDate()}日`;
                }
            }

            card.innerHTML = `
                <div class="trip-card-header">
                    <span class="trip-card-city">${trip.city}</span>
                    <span class="trip-card-days">${trip.days}天</span>
                </div>
                <h3 class="trip-card-title">${trip.title}</h3>
                <div class="trip-card-footer">
                    <span>共 ${trip.trip_days ? trip.trip_days.reduce((sum, day) => sum + (day.items ? day.items.length : 0), 0) : 0} 个景点</span>
                    <button class="delete-btn" onclick="deleteTrip(${trip.id}, event)">删除</button>
                </div>
                ${timeStr ? `<div class="trip-card-time">${timeStr}</div>` : ''}
            `;

            // 点击卡片加载行程
            card.addEventListener('click', (e) => {
                if (!e.target.classList.contains('delete-btn')) {
                    loadTripDetail(trip.id);
                }
            });

            grid.appendChild(card);
        });
    } catch (error) {
        console.error('Failed to load trips:', error);
        grid.innerHTML = '<div class="empty-state">加载失败，请稍后重试</div>';
    }
}

/**
 * 删除行程
 */
async function deleteTrip(tripId, event) {
    event.stopPropagation();

    if (!confirm('确定要删除这个行程吗？')) {
        return;
    }

    try {
        await api.deleteTrip(tripId);
        loadTripsList();
    } catch (error) {
        console.error('删除失败:', error);
        alert('删除失败，请重试');
    }
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', initApp);
