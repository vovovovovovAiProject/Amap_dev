/**
 * 高德地图封装
 */

class MapManager {
    constructor(containerId) {
        this.containerId = containerId;
        this.map = null;
        this.markers = [];
        this.polylines = [];
        this.infoWindow = null;
        this.is3D = false;
    }

    /**
     * 初始化地图
     */
    init() {
        this.map = new AMap.Map(this.containerId, {
            zoom: CONFIG.DEFAULT_ZOOM,
            center: CONFIG.DEFAULT_CENTER,
            mapStyle: 'amap://styles/whitesmoke',
            viewMode: '3D', // 开启3D模式
            pitch: 0
        });

        // 添加控件
        this.map.addControl(new AMap.Scale());

        // 开启实时交通图层
        this.trafficLayer = new AMap.TileLayer.Traffic({
            zIndex: 10,
            zooms: [7, 22]
        });
        this.trafficLayer.setMap(this.map);
        this.trafficVisible = true;

        // 创建信息窗体
        this.infoWindow = new AMap.InfoWindow({
            offset: new AMap.Pixel(0, -30)
        });

        console.log('地图初始化完成（含实时交通图层）');
    }

    /**
     * 切换实时交通图层
     */
    toggleTraffic() {
        if (!this.trafficLayer) return;

        this.trafficVisible = !this.trafficVisible;
        if (this.trafficVisible) {
            this.trafficLayer.show();
        } else {
            this.trafficLayer.hide();
        }
        return this.trafficVisible;
    }

    /**
     * 切换3D视角
     */
    toggle3DMode() {
        if (!this.map) return;

        this.is3D = !this.is3D;

        if (this.is3D) {
            this.map.setPitch(60);
            this.map.setRotation(15);
        } else {
            this.map.setPitch(0);
            this.map.setRotation(0);
        }

        return this.is3D;
    }

    /**
     * 添加POI标记
     */
    addPOIMarker(poi, index) {
        const position = poi.location.split(',').map(Number);

        // 创建自定义标记内容
        const markerContent = document.createElement('div');
        markerContent.className = 'custom-marker';
        markerContent.innerHTML = `
            <div class="marker-index">${index + 1}</div>
        `;
        markerContent.style.cssText = `
            width: 30px;
            height: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 14px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            cursor: pointer;
            transition: transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            border: 2px solid white;
        `;

        // 悬停缩放效果
        markerContent.onmouseenter = () => {
            markerContent.style.transform = 'scale(1.2) translateY(-2px)';
            markerContent.style.zIndex = '1000';
        };
        markerContent.onmouseleave = () => {
            markerContent.style.transform = 'scale(1) translateY(0)';
            markerContent.style.zIndex = 'auto';
        };

        const marker = new AMap.Marker({
            position: position,
            content: markerContent,
            offset: new AMap.Pixel(-15, -15)
        });

        // 点击事件
        marker.on('click', () => {
            this.showInfoWindow(poi, position);
        });

        marker.setMap(this.map);
        this.markers.push(marker);

        return marker;
    }

    /**
     * 显示信息窗体
     */
    showInfoWindow(poi, position) {
        // 尝试获取第一张图片
        let imageHtml = '';
        if (poi.photos && poi.photos.length > 0) {
            const photoUrl = poi.photos[0].url || poi.photos[0]; // 兼容对象或字符串
            imageHtml = `
                <div style="width: 100%; height: 120px; background-image: url('${photoUrl}'); background-size: cover; background-position: center; border-radius: 4px; margin-bottom: 8px;"></div>
            `;
        }

        // 获取经纬度
        const [lng, lat] = Array.isArray(position) ? position : position.toString().split(',');

        // 安全处理名称 - 使用 encodeURIComponent 编码
        const safeName = encodeURIComponent(poi.name || '目的地');

        // 转义HTML特殊字符
        const escapeHtml = (str) => {
            if (!str) return '';
            return str.replace(/&/g, '&amp;')
                      .replace(/</g, '&lt;')
                      .replace(/>/g, '&gt;')
                      .replace(/"/g, '&quot;')
                      .replace(/'/g, '&#39;');
        };

        const content = `
            <div style="padding: 10px; min-width: 240px; max-width: 300px;">
                ${imageHtml}
                <div style="display:flex; justify-content:space-between; align-items:start;">
                    <h4 style="margin: 0 0 6px 0; color: #1e293b; font-size: 16px;">${escapeHtml(poi.name)}</h4>
                    ${poi.rating ? `<span style="background:#fef3c7; color:#d97706; padding:2px 6px; border-radius:4px; font-size:12px; font-weight:bold;">${poi.rating}分</span>` : ''}
                </div>
                <p style="margin: 0 0 4px 0; color: #64748b; font-size: 13px; line-height: 1.4;">
                    📍 ${escapeHtml(poi.address || '暂无地址')}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                    <span style="color: #64748b; font-size: 12px; background: #f1f5f9; padding: 2px 6px; border-radius: 4px;">🏷️ ${escapeHtml(poi.type || '景点')}</span>
                    ${poi.cost ? `<span style="color: #ef4444; font-weight: 600; font-size: 14px;">¥${poi.cost}/人</span>` : ''}
                </div>
                <div style="display: flex; gap: 8px; margin-top: 12px; padding-top: 12px; border-top: 1px solid #e2e8f0;">
                    <button onclick="MapManager.navigateTo('${lng}', '${lat}', '${safeName}')"
                            style="flex: 1; padding: 8px 12px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px;">
                        🧭 导航
                    </button>
                    <button onclick="MapManager.callTaxi('${lng}', '${lat}', '${safeName}')"
                            style="flex: 1; padding: 8px 12px; background: linear-gradient(135deg, #f59e0b, #d97706); color: white; border: none; border-radius: 6px; font-size: 13px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px;">
                        🚕 打车
                    </button>
                </div>
            </div>
        `;

        this.infoWindow.setContent(content);
        this.infoWindow.open(this.map, position);
    }

    /**
     * 一键导航 - 跳转高德地图
     */
    static navigateTo(lng, lat, name) {
        // name 可能是 encodeURIComponent 编码过的，先解码
        const decodedName = decodeURIComponent(name);
        const url = `https://uri.amap.com/navigation?to=${lng},${lat},${encodeURIComponent(decodedName)}&mode=car&policy=1&src=mypage&coordinate=gaode&callnative=1`;
        window.open(url, '_blank');
    }

    /**
     * 一键打车 - 调用高德打车
     */
    static callTaxi(lng, lat, name) {
        // name 可能是 encodeURIComponent 编码过的，先解码
        const decodedName = decodeURIComponent(name);
        const url = `https://uri.amap.com/line?to=${lng},${lat},${encodeURIComponent(decodedName)}&mode=taxi&src=mypage&coordinate=gaode&callnative=1`;
        window.open(url, '_blank');
    }

    /**
     * 绘制路线
     */
    drawRoute(origin, destination, routeData) {
        let path = [];

        if (routeData && routeData.polyline) {
            // 解析 Polyline 字符串 (格式: "lng,lat;lng,lat;...")
            path = routeData.polyline.split(';').map(coordStr => {
                return coordStr.split(',').map(Number);
            });
        } else {
            // 降级：直线
            path = [
                origin.split(',').map(Number),
                destination.split(',').map(Number)
            ];
        }

        const polyline = new AMap.Polyline({
            path: path,
            strokeColor: '#10b981',
            strokeWeight: 5,
            strokeOpacity: 0.8,
            strokeStyle: 'solid',
            lineJoin: 'round',
            showDir: true // 显示箭头
        });

        polyline.setMap(this.map);
        this.polylines.push(polyline);

        return polyline;
    }

    /**
     * 显示行程
     */
    showTrip(tripData) {
        // 清除现有标记和路线
        this.clear();

        const { pois, routes } = tripData;
        const bounds = [];

        // 添加POI标记
        pois.forEach((poi, index) => {
            this.addPOIMarker(poi, index);
            const position = poi.location.split(',').map(Number);
            bounds.push(position);
        });

        // 绘制路线
        routes.forEach((route, index) => {
            if (index < pois.length - 1) {
                this.drawRoute(
                    pois[index].location,
                    pois[index + 1].location,
                    route
                );
            }
        });

        // 自动调整视野
        if (bounds.length > 0) {
            this.map.setFitView(this.markers);
        }
    }

    /**
     * 清除所有标记和路线
     */
    clear() {
        // 清除标记
        this.markers.forEach(marker => {
            marker.setMap(null);
        });
        this.markers = [];

        // 清除路线
        this.polylines.forEach(polyline => {
            polyline.setMap(null);
        });
        this.polylines = [];

        // 关闭信息窗体
        if (this.infoWindow) {
            this.infoWindow.close();
        }
    }

    /**
     * 缩放控制
     */
    zoomIn() {
        this.map.zoomIn();
    }

    zoomOut() {
        this.map.zoomOut();
    }

    /**
     * 定位到当前位置
     */
    locateCurrentPosition() {
        const geolocation = new AMap.Geolocation({
            enableHighAccuracy: true,
            timeout: 10000
        });

        geolocation.getCurrentPosition((status, result) => {
            if (status === 'complete') {
                this.map.setCenter([result.position.lng, result.position.lat]);
                this.map.setZoom(15);
            } else {
                console.error('定位失败:', result);
            }
        });
    }

    /**
     * 生成高德地图分享链接
     */
    generateShareUrl(pois) {
        if (!pois || pois.length === 0) return '';

        // 使用高德地图URI API
        const destination = pois[pois.length - 1];
        const destPosition = destination.location;

        // 构建高德地图导航链接
        const url = `https://uri.amap.com/navigation?to=${destPosition},${encodeURIComponent(destination.name)}&mode=car&policy=1&src=webapp&callnative=0`;

        return url;
    }
}
