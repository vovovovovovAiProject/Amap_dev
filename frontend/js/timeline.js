/**
 * 时间轴渲染模块
 */

class TimelineRenderer {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.currentPois = []; // 保存当前渲染的POI列表
    }

    /**
     * 渲染行程时间轴
     */
    render(tripData) {
        const { pois, routes } = tripData;
        this.container.innerHTML = '';
        this.currentPois = pois; // 保存POI列表供后续使用

        let currentTime = new Date();
        currentTime.setHours(9, 0, 0, 0); // 从早上9点开始

        pois.forEach((poi, index) => {
            // 渲染POI卡片
            const timeStr = this.formatTime(currentTime);
            this.container.appendChild(this.createPOICard(poi, timeStr, index));

            // 更新时间（加上游览时长）
            currentTime = new Date(currentTime.getTime() + (poi.duration || 60) * 60 * 1000);

            // 渲染交通卡片（如果不是最后一个POI）
            if (index < routes.length) {
                const route = routes[index];
                this.container.appendChild(this.createTransportCard(route));

                // 更新时间（加上交通时长）
                currentTime = new Date(currentTime.getTime() + (route.duration || 0) * 1000);
            }
        });
    }

    /**
     * 创建POI卡片
     */
    createPOICard(poi, time, index) {
        const item = document.createElement('div');
        item.className = 'timeline-item poi';

        // 解析位置，确保有默认值
        const location = poi.location || '116.397428,39.90923';
        const [lng, lat] = location.split(',');
        const poiName = poi.name || '目的地';

        item.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-poi-card" data-index="${index}">
                <div class="poi-header">
                    <span class="poi-time">${time}</span>
                    <span class="poi-duration">🕐 ${poi.visit_duration || poi.duration || 60}分钟</span>
                </div>
                <h4 class="poi-name">${this.escapeHtml(poi.name)}</h4>
                <span class="poi-type">${this.escapeHtml(poi.type || '景点')}</span>
                <p class="poi-address">📍 ${this.escapeHtml(poi.address || '暂无地址')}</p>
                <div class="poi-footer">
                    <span class="poi-cost">${poi.cost ? '💰 ¥' + poi.cost : '免费'}</span>
                </div>
                <div class="poi-actions">
                    <button class="poi-action-btn nav-btn" data-action="nav" data-lng="${lng}" data-lat="${lat}" data-name="${this.escapeHtml(poiName)}" data-index="${index}">
                        🧭 导航
                    </button>
                    <button class="poi-action-btn taxi-btn" data-action="taxi" data-lng="${lng}" data-lat="${lat}" data-name="${this.escapeHtml(poiName)}" data-index="${index}">
                        🚕 打车
                    </button>
                    <button class="poi-action-btn map-btn" data-action="map" data-lng="${lng}" data-lat="${lat}" data-name="${this.escapeHtml(poiName)}" data-index="${index}">
                        🗺️ 地图
                    </button>
                </div>
            </div>
        `;

        // 使用事件委托绑定按钮事件
        const actionsDiv = item.querySelector('.poi-actions');
        actionsDiv.addEventListener('click', (e) => {
            const btn = e.target.closest('.poi-action-btn');
            if (!btn) return;

            e.preventDefault();
            e.stopPropagation();

            const action = btn.dataset.action;
            const poiLng = btn.dataset.lng;
            const poiLat = btn.dataset.lat;
            const name = btn.dataset.name;

            if (!poiLng || !poiLat) {
                alert('无法获取位置信息');
                return;
            }

            switch (action) {
                case 'nav':
                    TimelineRenderer.navigateTo(poiLng, poiLat, name);
                    break;
                case 'taxi':
                    TimelineRenderer.callTaxi(poiLng, poiLat, name);
                    break;
                case 'map':
                    // 直接使用按钮上的数据，不依赖全局变量
                    TimelineRenderer.showOnMapByLocation(poiLng, poiLat, name);
                    break;
            }
        });

        return item;
    }

    /**
     * HTML转义，防止XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * 创建交通卡片
     */
    createTransportCard(route) {
        const item = document.createElement('div');
        item.className = 'timeline-item transport';

        const icon = CONFIG.TRANSPORT_ICONS[route.transport_mode] || '🚶';
        const modeName = CONFIG.TRANSPORT_NAMES[route.transport_mode] || '步行';
        const distance = this.formatDistance(route.distance);
        const duration = this.formatDuration(route.duration);

        item.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-transport-card">
                <div class="transport-icon ${route.transport_mode}">${icon}</div>
                <div class="transport-info">
                    <div class="transport-mode">${modeName}</div>
                    <div class="transport-detail">${distance} · ${duration}</div>
                </div>
                <div class="transport-cost">${route.cost ? '¥' + route.cost : ''}</div>
            </div>
        `;

        return item;
    }

    /**
     * 一键导航 - 跳转高德地图导航
     */
    static navigateTo(lng, lat, name) {
        if (!lng || !lat) {
            alert('无法获取位置信息');
            return;
        }
        // 高德地图URI API - 导航
        const url = `https://uri.amap.com/navigation?to=${lng},${lat},${encodeURIComponent(name)}&mode=car&policy=1&src=mypage&coordinate=gaode&callnative=1`;
        window.open(url, '_blank');
    }

    /**
     * 一键打车 - 调用高德打车服务
     */
    static callTaxi(lng, lat, name) {
        if (!lng || !lat) {
            alert('无法获取位置信息');
            return;
        }
        // 高德地图URI API - 打车
        const url = `https://uri.amap.com/line?to=${lng},${lat},${encodeURIComponent(name)}&mode=taxi&src=mypage&coordinate=gaode&callnative=1`;
        window.open(url, '_blank');
    }

    /**
     * 在地图上显示 - 通过经纬度和名称
     */
    static showOnMapByLocation(lng, lat, name) {
        try {
            const position = [parseFloat(lng), parseFloat(lat)];

            // 先切换到地图标签
            if (typeof switchTab === 'function') {
                switchTab('map');
            }

            // 延迟执行地图操作，确保地图已初始化
            setTimeout(() => {
                if (mapManager && mapManager.map) {
                    mapManager.map.setCenter(position);
                    mapManager.map.setZoom(16);

                    // 构造简单的 POI 对象用于显示信息窗体
                    const poi = {
                        name: name,
                        location: `${lng},${lat}`,
                        address: '',
                        type: '景点'
                    };
                    mapManager.showInfoWindow(poi, position);
                }
            }, 200);
        } catch (error) {
            console.error('显示地图失败:', error);
            alert('显示地图失败，请重试');
        }
    }

    /**
     * 在地图上显示 - 通过索引（保留兼容）
     */
    static showOnMap(index) {
        if (tripData && tripData.pois && tripData.pois[index]) {
            const poi = tripData.pois[index];
            if (!poi.location) {
                alert('无法获取位置信息');
                return;
            }
            const [lng, lat] = poi.location.split(',');
            TimelineRenderer.showOnMapByLocation(lng, lat, poi.name);
        } else {
            alert('无法获取景点信息');
        }
    }

    /**
     * 格式化时间
     */
    formatTime(date) {
        const hours = date.getHours().toString().padStart(2, '0');
        const minutes = date.getMinutes().toString().padStart(2, '0');
        return `${hours}:${minutes}`;
    }

    /**
     * 格式化距离
     */
    formatDistance(meters) {
        if (meters >= 1000) {
            return (meters / 1000).toFixed(1) + 'km';
        }
        return meters + 'm';
    }

    /**
     * 格式化时长
     */
    formatDuration(seconds) {
        const minutes = Math.round(seconds / 60);
        if (minutes >= 60) {
            const hours = Math.floor(minutes / 60);
            const mins = minutes % 60;
            return `${hours}小时${mins}分钟`;
        }
        return `${minutes}分钟`;
    }
}
