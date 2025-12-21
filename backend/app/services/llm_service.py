"""
通义千问LLM服务封装
用于解析用户自然语言输入，生成行程规划
"""

import os
import json
import httpx
from typing import List, AsyncGenerator
from dotenv import load_dotenv

load_dotenv()


class LLMService:
    """通义千问大模型服务"""

    def __init__(self):
        self.api_key = os.getenv("QWEN_API_KEY", "")
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.model = "qwen-turbo"

    async def _chat(self, messages: List[dict], response_format: str = "text") -> str:
        """调用通义千问API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "result_format": "message"
            }
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()

            # 提取回复内容
            output = result.get("output", {})
            choices = output.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""

    async def _chat_stream(self, messages: List[dict]) -> AsyncGenerator[str, None]:
        """流式调用通义千问API"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable"
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "result_format": "message",
                "incremental_output": True
            }
        }

        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream(
                "POST",
                self.base_url,
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data:"):
                        try:
                            data = json.loads(line[5:])
                            output = data.get("output", {})
                            choices = output.get("choices", [])
                            if choices:
                                content = choices[0].get("message", {}).get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

    async def chat_stream(self, message: str, system_prompt: str = None) -> AsyncGenerator[str, None]:
        """流式对话接口"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        async for chunk in self._chat_stream(messages):
            yield chunk
    
    def _extract_json(self, response: str):
        """Helper to extract JSON from LLM response"""
        try:
            # Cleanup markdown code blocks
            if "```" in response:
                # Try to find the block closest to being JSON
                blocks = response.split("```")
                for block in blocks:
                    block = block.strip()
                    if block.startswith("json"):
                        block = block[4:].strip()
                    if (block.startswith("{") and block.endswith("}")) or \
                       (block.startswith("[") and block.endswith("]")):
                        return json.loads(block)
            
            # Identify potential JSON start and end
            response = response.strip()
            
            # Try parsing directly
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                pass

            # Try finding array or object
            if "{" in response and "}" in response:
                start = response.find("{")
                end = response.rfind("}") + 1
                return json.loads(response[start:end])
            elif "[" in response and "]" in response:
                start = response.find("[")
                end = response.rfind("]") + 1
                return json.loads(response[start:end])
                
        except Exception:
            pass
        return None

    async def parse_user_intent(self, user_input: str) -> dict:
        """
        解析用户自然语言输入，提取出行意图
        """
        system_prompt = """你是一个旅行规划助手，负责解析用户的出行需求。
请从用户输入中提取以下信息，以JSON格式返回：

{
    "city": "目的地城市",
    "duration": 天数（数字）,
    "travelers": ["同行人类型，如：老人、小孩、情侣等"],
    "preferences": ["偏好，如：文化、美食、自然等"],
    "budget": 预算金额（数字，如果没提到则为null）,
    "keywords": ["明确提到的景点或地点"],
    "poi_type": "主要POI类型，如：风景名胜、博物馆、餐饮等",
    "constraints": ["特殊约束，如：少走路、避开人群等"]
}

只返回JSON，不要其他内容。如果某项信息用户没有提供，使用合理的默认值或null。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        response = await self._chat(messages)
        
        data = self._extract_json(response)
        if data and isinstance(data, dict):
            return data
            
        # 解析失败，返回默认值
        return {
            "city": "北京",
            "duration": 1,
            "travelers": [],
            "preferences": ["观光"],
            "budget": None,
            "keywords": [],
            "poi_type": None,
            "constraints": []
        }
    
    async def generate_trip_summary(
        self,
        pois: List[dict],
        routes: List[dict],
        weather: dict
    ) -> str:
        """生成行程摘要"""
        
        # 构建POI列表描述
        poi_desc = "\n".join([
            f"- {poi.get('name')}: {poi.get('type', '景点')}"
            for poi in pois
        ])
        
        # 天气描述
        weather_desc = ""
        if weather and weather.get("casts"):
            today = weather["casts"][0]
            weather_desc = f"今日天气：{today.get('dayweather')}，{today.get('daytemp')}°C"
        
        system_prompt = """你是一个旅行规划助手，请根据以下信息生成一段简洁的行程摘要（2-3句话）。
摘要应该包含：主要景点、大致时长、天气提醒（如果有）。
语气要亲切友好，像朋友推荐一样。"""
        
        user_content = f"""行程包含以下景点：
{poi_desc}

{weather_desc}

请生成简短的行程摘要。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        return await self._chat(messages)
    
    async def optimize_trip_order(
        self,
        pois: List[dict],
        constraints: List[str]
    ) -> List[dict]:
        """优化行程顺序"""
        
        poi_names = [poi.get("name") for poi in pois]
        
        system_prompt = """你是一个旅行规划助手，请根据景点列表和约束条件，给出最优的游览顺序。
考虑因素：地理位置接近的景点放在一起、景点开放时间、游览时长等。
只返回景点名称列表的JSON数组，按推荐游览顺序排列。"""
        
        user_content = f"""景点列表：{json.dumps(poi_names, ensure_ascii=False)}
约束条件：{json.dumps(constraints, ensure_ascii=False)}

请返回优化后的景点顺序（JSON数组）。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = await self._chat(messages)
        
        ordered_names = self._extract_json(response)
        
        if ordered_names and isinstance(ordered_names, list):
            # 按新顺序重排POI
            name_to_poi = {poi.get("name"): poi for poi in pois}
            # 过滤掉不存在的名称（防止LLM幻觉）
            return [name_to_poi[name] for name in ordered_names if name in name_to_poi]
            
        return pois  # 解析失败返回原顺序
    
    async def plan_multi_day_trip(
        self,
        pois: List[dict],
        days: int,
        city: str
    ) -> List[dict]:
        """
        多日行程规划
        智能将景点分配到每一天，并优化每天的顺序
        
        返回格式:
        [
            {
                "day": 1,
                "pois": [poi1, poi2...]
            },
            ...
        ]
        """
        poi_names = [poi.get("name") for poi in pois]
        
        system_prompt = """你是一个专业的旅行规划师。请将给定的景点列表分配到指定的天数中，并为每一天规划合理的游览顺序。
考虑因素：
1. 地理位置临近的景点安排在同一天
2. 每天的游览强度要适中
3. 考虑景点的最佳游览时间

请返回 JSON 数组，格式如下：
[
    {
        "day": 1,
        "summary": "今日主题：漫步古都。我们将游览...",
        "pois": ["景点A", "景点B"...]
    },
    ...
]"""
        
        user_content = f"""目的地：{city}
天数：{days}
景点列表：{json.dumps(poi_names, ensure_ascii=False)}

请规划每天的行程（返回JSON数组）。"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = await self._chat(messages)
        
        day_plans = self._extract_json(response)
        
        result = []
        name_to_poi = {poi.get("name"): poi for poi in pois}
        
        if day_plans and isinstance(day_plans, list):
            for day_plan in day_plans:
                day_index = day_plan.get("day", 1)
                day_poi_names = day_plan.get("pois", [])
                
                # 匹配真实POI对象
                day_pois = []
                for name in day_poi_names:
                    if name in name_to_poi:
                        day_pois.append(name_to_poi[name])
                
                if day_pois:
                    result.append({
                        "day": day_index,
                        "summary": day_plan.get("summary", ""),
                        "pois": day_pois
                    })
        
        # 如果解析失败或结果为空，简单的平均分配作为兜底
        if not result:
            avg = len(pois) // days + 1
            if avg == 0: avg = 1
            
            current_day = 1
            for i in range(0, len(pois), avg):
                day_slice = pois[i:i + avg]
                if day_slice:
                    result.append({
                        "day": current_day,
                        "pois": day_slice
                    })
                    current_day += 1
                if current_day > days:
                    # 剩下的都放到最后一天
                    if i + avg < len(pois):
                        result[-1]["pois"].extend(pois[i + avg:])
                    break
                    
        return result
                    
    async def generate_travel_insights(
        self,
        city: str,
        days: int,
        weather: dict,
        pois: List[dict]
    ) -> dict:
        """生成深度旅行洞察"""
        
        poi_list = [p.get("name") for p in pois[:10]]
        weather_info = "暂无天气信息"
        if weather and weather.get("casts"):
            cast = weather["casts"][0]
            weather_info = f"{cast.get('dayweather')}, {cast.get('daytemp')}°C"

        system_prompt = """你是一个资深的旅行专家和地道生活家。根据目的地、天数、天气和景点列表，生成一份深度的旅行智囊建议。
请以JSON格式返回：
{
    "packing_list": ["根据天气和行程建议的3-5件必备物品"],
    "local_delicacies": ["3-4种目的地必吃特色美食名称"],
    "pro_tips": ["3条避坑指南、习俗提示或游玩秘籍"]
}
只返回JSON，内容要专业、真实、有吸引力。"""

        user_content = f"""目的地：{city}
天数：{days}天
今日天气：{weather_info}
主要景点：{", ".join(poi_list)}

请生成旅行智囊建议。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        response = await self._chat(messages)
        data = self._extract_json(response)
        
        # 确保返回的是符合要求的字典结构
        if data and isinstance(data, dict):
            # 防御性转换：确保每一项都是列表
            for key in ["packing_list", "local_delicacies", "pro_tips"]:
                val = data.get(key)
                if not isinstance(val, list):
                    if val and isinstance(val, str):
                        data[key] = [v.strip() for v in val.replace("、", ",").replace("，", ",").split(",") if v.strip()]
                    else:
                        data[key] = []
            return data
            
        print(f"Failed to parse insights JSON: {response}")
        return {
            "packing_list": ["雨伞", "充电宝", "舒适的运动鞋"],
            "local_delicacies": ["地道特色美食"],
            "pro_tips": ["建议提前预订热门景点门票"]
        }

    async def analyze_chat_intent(self, message: str, current_trip: dict = None, conversation_context: list = None) -> dict:
        """
        分析对话意图 - 简化版，更灵活自然
        """
        has_trip = current_trip is not None and current_trip.get("days")

        # 构建对话历史上下文
        context_str = ""
        collected_from_history = {}
        if conversation_context:
            context_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_context[-8:]])
            # 从历史中提取已收集的信息
            full_context = " ".join([msg['content'] for msg in conversation_context])
            # 简单的信息提取
            import re
            city_patterns = ['去(\\w{2,4})[玩游旅]', '(\\w{2,4})旅[游行]', '到(\\w{2,4})', '在(\\w{2,4})']
            for pattern in city_patterns:
                match = re.search(pattern, full_context)
                if match:
                    collected_from_history['city'] = match.group(1)
                    break

        system_prompt = f"""你是"智途无忧"的AI旅行助手，性格活泼、专业、贴心。像朋友一样和用户聊天，帮他们规划完美旅程。

【当前状态】
- 用户{'已有行程' if has_trip else '还没有行程'}
- 对话历史：
{context_str if context_str else '（这是新对话的开始）'}

【你的任务】
理解用户意图，自然地推进对话。核心目标是帮用户规划出满意的行程。

【意图判断 - 简单直接】

🎯 generate_trip（立即生成行程）：
- 用户明确说了城市+天数，如"去杭州玩3天"、"北京两日游"
- 用户确认了之前的总结，如"好的"、"可以"、"行"、"没问题"、"开始吧"
- 用户催促生成，如"帮我规划"、"开始吧"、"生成行程"
- 【重要】只要有城市和天数，就可以生成！其他信息都是可选的

💬 chat（自然聊天）：
- 用户问问题、闲聊、询问建议
- 如"大连有什么好玩的"、"推荐一下"、"你觉得呢"
- 给出有价值的回答，展示你的专业性

❓ ask_questions（收集信息）：
- 缺少关键信息（城市或天数）时，友好地询问
- 【重要】不要啰嗦！一次只问1-2个问题
- 【重要】用户说"随便"、"都行"、"没有特别的"时，不要再追问，直接进入下一步

✅ confirm_info（确认信息）：
- 已有城市+天数，简单确认一下就开始规划
- 不要列太多细节，简洁明了

🔧 modify_trip（修改行程）：
- 用户想调整现有行程

【回复风格】
- 简洁有趣，不要长篇大论
- 适当用emoji增加亲和力
- 像朋友聊天，不要太正式
- 给出具体有用的建议，不要泛泛而谈

【返回JSON格式】
{{
    "action": "generate_trip" | "chat" | "ask_questions" | "confirm_info" | "modify_trip",
    "reply": "你的回复（简洁自然）",
    "collected_info": {{
        "city": "城市名",
        "duration": 天数,
        "travelers": "同行人",
        "preferences": ["偏好"],
        "special_needs": "特殊需求"
    }},
    "ready_to_generate": true或false
}}

只返回JSON，不要其他内容。"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]

        response = await self._chat(messages)
        data = self._extract_json(response)

        if data and isinstance(data, dict):
            # 合并从历史中提取的信息
            if collected_from_history:
                existing_info = data.get("collected_info", {})
                for k, v in collected_from_history.items():
                    if k not in existing_info or not existing_info[k]:
                        existing_info[k] = v
                data["collected_info"] = existing_info
            return data

        # 默认友好回复
        return {
            "action": "ask_questions",
            "reply": "嗨！想去哪里玩呀？告诉我目的地和天数，我来帮你规划~ 🗺️",
            "collected_info": collected_from_history,
            "missing_info": ["city", "duration"],
            "ready_to_generate": False
        }
