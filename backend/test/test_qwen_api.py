"""
通义千问 (百炼平台) API 测试
"""

import os
import httpx
import asyncio
import json
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"


async def test_basic_chat():
    """测试基础对话"""
    print("\n" + "=" * 50)
    print("🤖 测试1: 基础对话")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "system", "content": "你是一个友好的助手"},
                {"role": "user", "content": "你好，请用一句话介绍自己"}
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(BASE_URL, headers=headers, json=payload)
            data = response.json()
            
            if "output" in data:
                choices = data["output"].get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    print(f"✅ 成功!")
                    print(f"   回复: {content[:100]}...")
                    return True
            
            # 检查错误信息
            if "code" in data:
                print(f"❌ 失败: {data.get('message', '未知错误')}")
                print(f"   错误码: {data.get('code')}")
            else:
                print(f"❌ 失败: 响应格式异常")
                print(f"   响应: {json.dumps(data, ensure_ascii=False)[:200]}")
            return False
            
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False


async def test_intent_parsing():
    """测试意图解析（行程规划场景）"""
    print("\n" + "=" * 50)
    print("🤖 测试2: 意图解析（行程规划）")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """你是一个旅行规划助手，负责解析用户的出行需求。
请从用户输入中提取以下信息，以JSON格式返回：
{
    "city": "目的地城市",
    "duration": 天数,
    "keywords": ["明确提到的景点"],
    "preferences": ["偏好"]
}
只返回JSON，不要其他内容。"""

    user_input = "周末想带爸妈去北京玩，想去故宫和天安门"
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(BASE_URL, headers=headers, json=payload)
            data = response.json()
            
            if "output" in data:
                choices = data["output"].get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    print(f"✅ 成功!")
                    print(f"   用户输入: {user_input}")
                    print(f"   解析结果:")
                    
                    # 尝试解析JSON
                    try:
                        # 移除可能的markdown标记
                        json_str = content
                        if "```json" in json_str:
                            json_str = json_str.split("```json")[1].split("```")[0]
                        elif "```" in json_str:
                            json_str = json_str.split("```")[1].split("```")[0]
                        
                        parsed = json.loads(json_str.strip())
                        print(f"   {json.dumps(parsed, ensure_ascii=False, indent=2)}")
                    except:
                        print(f"   {content}")
                    return True
            
            if "code" in data:
                print(f"❌ 失败: {data.get('message', '未知错误')}")
            return False
            
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False


async def test_trip_summary():
    """测试行程摘要生成"""
    print("\n" + "=" * 50)
    print("🤖 测试3: 行程摘要生成")
    print("=" * 50)
    
    headers = {
        "Authorization": f"Bearer {QWEN_API_KEY}",
        "Content-Type": "application/json"
    }
    
    system_prompt = """你是一个旅行规划助手，请根据景点列表生成一段简短的行程摘要（2-3句话）。
语气要亲切友好，像朋友推荐一样。"""

    user_input = """行程包含以下景点：
- 天安门广场：风景名胜
- 故宫博物院：博物馆
- 景山公园：公园

今日天气：晴，25°C

请生成简短的行程摘要。"""
    
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
        },
        "parameters": {
            "result_format": "message"
        }
    }
    
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(BASE_URL, headers=headers, json=payload)
            data = response.json()
            
            if "output" in data:
                choices = data["output"].get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    print(f"✅ 成功!")
                    print(f"   生成的摘要:")
                    print(f"   {content}")
                    return True
            
            if "code" in data:
                print(f"❌ 失败: {data.get('message', '未知错误')}")
            return False
            
        except Exception as e:
            print(f"❌ 请求异常: {str(e)}")
            return False


async def main():
    print("\n" + "🤖 " + "=" * 46 + " 🤖")
    print("       通义千问 (百炼平台) API 测试")
    print("🤖 " + "=" * 46 + " 🤖")
    
    if not QWEN_API_KEY:
        print("\n❌ 错误: 未找到 QWEN_API_KEY 环境变量")
        print("   请在 backend/.env 文件中设置 QWEN_API_KEY")
        return
    
    print(f"\n📌 API Key: {QWEN_API_KEY[:8]}...{QWEN_API_KEY[-4:]}")
    
    results = []
    results.append(await test_basic_chat())
    results.append(await test_intent_parsing())
    results.append(await test_trip_summary())
    
    print("\n" + "=" * 50)
    print("📊 测试结果汇总")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"\n🎉 全部通过! {passed}/{total}")
    else:
        print(f"\n⚠️ 通过 {passed}/{total}")
    
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
