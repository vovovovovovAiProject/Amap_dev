"""
运行所有API测试
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def main():
    print("\n")
    print("🚀 " + "=" * 50 + " 🚀")
    print("          智途无忧 - API 测试套件")
    print("🚀 " + "=" * 50 + " 🚀")
    
    print("\n" + "-" * 54)
    print("📍 开始测试高德地图 API...")
    print("-" * 54)
    
    from test_amap_api import main as test_amap
    await test_amap()
    
    print("\n" + "-" * 54)
    print("🤖 开始测试通义千问 API...")
    print("-" * 54)
    
    from test_qwen_api import main as test_qwen
    await test_qwen()
    
    print("\n" + "=" * 54)
    print("✅ 所有测试完成!")
    print("=" * 54 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
