/**
 * 配置文件
 */

const CONFIG = {
    // API基础地址 - 使用相对路径以支持合并部署
    API_BASE_URL: '/api/v1',

    // 高德地图配置
    AMAP_KEY: '<api-key>', // 替换为你的高德Key
    AMAP_VERSION: '2.0',

    // 默认城市
    DEFAULT_CITY: '北京',

    // 默认地图中心点（北京天安门）
    DEFAULT_CENTER: [116.397428, 39.90923],
    DEFAULT_ZOOM: 12,

    // 交通方式图标
    TRANSPORT_ICONS: {
        walking: '🚶',
        transit: '🚇',
        driving: '🚗',
        riding: '🚴'
    },

    // 交通方式名称
    TRANSPORT_NAMES: {
        walking: '步行',
        transit: '公共交通',
        driving: '驾车',
        riding: '骑行'
    }
};

// 防止被修改
Object.freeze(CONFIG);
