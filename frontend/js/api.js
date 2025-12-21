/**
 * API请求封装
 */

class API {
    constructor() {
        this.baseUrl = CONFIG.API_BASE_URL;
    }

    /**
     * 发送请求
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;

        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        try {
            const response = await fetch(url, { ...defaultOptions, ...options });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API请求失败:', error);
            throw error;
        }
    }

    /**
     * GET请求
     */
    async get(endpoint, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const url = queryString ? `${endpoint}?${queryString}` : endpoint;
        return this.request(url, { method: 'GET' });
    }

    /**
     * POST请求
     */
    async post(endpoint, data = {}) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    /**
     * 生成行程
     */
    async generateTrip(userInput, startLocation = null) {
        return this.post('/trip/generate', {
            user_input: userInput,
            start_location: startLocation
        });
    }

    /**
     * 搜索POI
     */
    async searchPOI(keyword, city = CONFIG.DEFAULT_CITY) {
        return this.get('/poi/search', { keyword, city });
    }

    /**
     * 获取天气
     */
    async getWeather(city = CONFIG.DEFAULT_CITY) {
        return this.get('/weather', { city });
    }

    /**
     * 规划路线
     */
    async planRoute(origin, destination, mode = 'transit') {
        return this.get('/route/plan', { origin, destination, mode });
    }

    /**
     * 保存行程
     */
    async saveTrip(tripData) {
        return this.post('/trip/save', tripData);
    }

    /**
     * 获取行程列表
     */
    async listTrips() {
        return this.get('/trip/list');
    }

    /**
     * 获取行程详情
     */
    async getTripDetail(id) {
        return this.get(`/trip/${id}`);
    }

    /**
     * 删除行程
     */
    async deleteTrip(id) {
        return this.request(`/trip/${id}`, { method: 'DELETE' });
    }

    /**
     * 对话接口
     */
    async chat(data) {
        return this.post('/chat', data);
    }

    /**
     * 流式对话接口
     * @param {Object} data - 请求数据
     * @param {Function} onChunk - 收到数据块时的回调
     * @param {Function} onDone - 完成时的回调
     * @param {Function} onError - 错误时的回调
     * @param {Function} onSearch - 搜索开始时的回调，参数为搜索结果数组
     */
    async chatStream(data, onChunk, onDone, onError, onSearch) {
        const url = `${this.baseUrl}/chat/stream`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const text = decoder.decode(value, { stream: true });
                const lines = text.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            if (data.search) {
                                onSearch && onSearch(data.search_results || []);
                            }
                            if (data.content) {
                                onChunk(data.content);
                            }
                            if (data.done) {
                                onDone && onDone();
                            }
                            if (data.error) {
                                onError && onError(data.error);
                            }
                        } catch (e) {
                            // 忽略解析错误
                        }
                    }
                }
            }
        } catch (error) {
            console.error('流式请求失败:', error);
            onError && onError(error.message);
        }
    }

    /**
     * 联网搜索接口
     */
    async search(query, city = null, searchType = 'general') {
        const params = { query };
        if (city) params.city = city;
        if (searchType) params.search_type = searchType;
        return this.get('/search', params);
    }
}

// 创建全局实例
const api = new API();
