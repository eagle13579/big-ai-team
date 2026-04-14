#!/usr/bin/env python3
"""
性能测试脚本，验证系统性能优化效果
"""

import asyncio
import json
import statistics
import threading
import time

import aiohttp

# 测试配置
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/tasks"
CONCURRENT_USERS = 100  # 并发用户数
REQUESTS_PER_USER = 10  # 每个用户的请求数
TOTAL_REQUESTS = CONCURRENT_USERS * REQUESTS_PER_USER

# 测试场景
test_scenarios = [
    {
        "name": "test_calculation",
        "payload": {
            "query": "计算 1+1",
            "max_steps": 5
        }
    },
    {
        "name": "test_web_search",
        "payload": {
            "query": "搜索 Python 编程",
            "max_steps": 5
        }
    },
    {
        "name": "test_code_execution",
        "payload": {
            "query": "执行 Python 代码 print(1+1)",
            "max_steps": 5
        }
    },
    {
        "name": "test_data_analysis",
        "payload": {
            "query": "分析数据文件",
            "max_steps": 5
        }
    }
]

# 测试结果
results = []
error_count = 0
lock = threading.Lock()

async def get_auth_token(session):
    """获取认证令牌"""
    auth_data = {
        "username": "admin",
        "password": "admin123",
        "grant_type": "password"
    }
    try:
        async with session.post(f"{BASE_URL}/api/v1/auth/token", data=auth_data) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("access_token")
            else:
                print(f"获取认证令牌失败: {response.status}")
                print(f"响应内容: {await response.text()}")
                return None
    except Exception as e:
        print(f"获取认证令牌异常: {str(e)}")
        return None

async def make_request(session, scenario, token):
    """发送单个请求并记录结果"""
    global error_count
    start_time = time.time()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    try:
        async with session.post(f"{BASE_URL}{ENDPOINT}", json=scenario["payload"], headers=headers) as response:
            end_time = time.time()
            response_time = end_time - start_time
            status_code = response.status
            
            with lock:
                results.append({
                    "scenario": scenario["name"],
                    "status_code": status_code,
                    "response_time": response_time
                })
                if status_code != 200:
                    error_count += 1
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        with lock:
            results.append({
                "scenario": scenario["name"],
                "status_code": 0,
                "response_time": response_time,
                "error": str(e)
            })
            error_count += 1

async def run_user(session, user_id, token):
    """模拟单个用户的请求"""
    for _ in range(REQUESTS_PER_USER):
        # 随机选择一个测试场景
        scenario = test_scenarios[user_id % len(test_scenarios)]
        await make_request(session, scenario, token)
        # 随机等待时间
        await asyncio.sleep(0.1)

async def main():
    """主测试函数"""
    print("开始性能测试...")
    print(f"并发用户数: {CONCURRENT_USERS}")
    print(f"每个用户请求数: {REQUESTS_PER_USER}")
    print(f"总请求数: {TOTAL_REQUESTS}")
    print(f"测试场景: {[scenario['name'] for scenario in test_scenarios]}")
    print("=" * 80)
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        # 获取认证令牌
        token = await get_auth_token(session)
        if not token:
            print("无法获取认证令牌，测试终止")
            return
        
        tasks = []
        for i in range(CONCURRENT_USERS):
            task = asyncio.create_task(run_user(session, i, token))
            tasks.append(task)
        
        # 等待所有任务完成
        await asyncio.gather(*tasks)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # 计算统计数据
    response_times = [r["response_time"] for r in results]
    success_count = len([r for r in results if r["status_code"] == 200])
    success_rate = success_count / TOTAL_REQUESTS * 100
    error_rate = error_count / TOTAL_REQUESTS * 100
    
    print("=" * 80)
    print("测试结果:")
    print(f"总耗时: {total_time:.2f} 秒")
    print(f"总请求数: {TOTAL_REQUESTS}")
    print(f"成功请求数: {success_count}")
    print(f"失败请求数: {error_count}")
    print(f"成功率: {success_rate:.2f}%")
    print(f"错误率: {error_rate:.2f}%")
    print(f"平均响应时间: {statistics.mean(response_times):.4f} 秒")
    if response_times:
        print(f"95% 响应时间: {sorted(response_times)[int(len(response_times) * 0.95)]:.4f} 秒")
        print(f"99% 响应时间: {sorted(response_times)[int(len(response_times) * 0.99)]:.4f} 秒")
    print(f"吞吐量: {TOTAL_REQUESTS / total_time:.2f} QPS")
    
    # 按场景统计
    print("\n按场景统计:")
    for scenario in test_scenarios:
        scenario_results = [r for r in results if r["scenario"] == scenario["name"]]
        if scenario_results:
            scenario_response_times = [r["response_time"] for r in scenario_results]
            scenario_success_count = len([r for r in scenario_results if r["status_code"] == 200])
            scenario_success_rate = scenario_success_count / len(scenario_results) * 100
            print(f"{scenario['name']}:")
            print(f"  平均响应时间: {statistics.mean(scenario_response_times):.4f} 秒")
            print(f"  成功率: {scenario_success_rate:.2f}%")
    
    # 保存结果到文件
    with open("performance_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_requests": TOTAL_REQUESTS,
            "success_count": success_count,
            "error_count": error_count,
            "total_time": total_time,
            "average_response_time": statistics.mean(response_times) if response_times else 0,
            "95th_percentile": sorted(response_times)[int(len(response_times) * 0.95)] if response_times else 0,
            "99th_percentile": sorted(response_times)[int(len(response_times) * 0.99)] if response_times else 0,
            "throughput": TOTAL_REQUESTS / total_time,
            "results": results
        }, f, ensure_ascii=False, indent=2)
    
    print("\n测试结果已保存到 performance_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
