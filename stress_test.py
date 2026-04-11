#!/usr/bin/env python3
"""
压力测试脚本，模拟对 Agent-Reach 技能的并发请求
"""

import asyncio
import json
import random
import statistics
import threading
import time

import aiohttp

# 测试配置
BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/agent-reach/execute"
CONCURRENT_USERS = 100  # 并发用户数
REQUESTS_PER_USER = 10  # 每个用户的请求数
TOTAL_REQUESTS = CONCURRENT_USERS * REQUESTS_PER_USER

# 测试场景
test_scenarios = [
    {
        "name": "read_webpage",
        "payload": {
            "action": "read_webpage",
            "params": {"url": "https://example.com"}
        }
    },
    {
        "name": "search_twitter",
        "payload": {
            "action": "search_twitter",
            "params": {"query": "AI Agent", "limit": 5}
        }
    },
    {
        "name": "get_youtube_transcript",
        "payload": {
            "action": "get_youtube_transcript",
            "params": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        }
    },
    {
        "name": "search_github_repos",
        "payload": {
            "action": "search_github_repos",
            "params": {"query": "AI Agent", "language": "python"}
        }
    }
]

# 测试结果
results = []
error_count = 0
lock = threading.Lock()


class RetryMechanism:
    """
    重试机制，用于处理临时错误
    """
    def __init__(self, max_retries=3, backoff_factor=0.5, retryable_status_codes=(429, 500, 502, 503, 504)):
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.retryable_status_codes = retryable_status_codes
    
    async def execute(self, func, *args, **kwargs):
        """
        执行函数并在失败时重试
        """
        retries = 0
        while retries <= self.max_retries:
            try:
                return await func(*args, **kwargs)
            except aiohttp.ClientError:
                if retries >= self.max_retries:
                    raise
                retries += 1
                wait_time = self.backoff_factor * (2 ** (retries - 1)) + random.uniform(0, 0.1)
                await asyncio.sleep(wait_time)
            except Exception:
                # 其他异常不重试
                raise


class CircuitBreaker:
    """
    熔断机制，防止级联失败
    """
    def __init__(self, failure_threshold=5, recovery_time=30, timeout=5):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.timeout = timeout
        self.failure_count = 0
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.last_failure_time = 0
    
    def is_allowed(self):
        """
        检查是否允许请求
        """
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_time:
                self.state = "HALF_OPEN"
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """
        记录成功
        """
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.failure_count = 0
    
    def record_failure(self):
        """
        记录失败
        """
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.state == "CLOSED" and self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
        elif self.state == "HALF_OPEN":
            self.state = "OPEN"


class ServiceDegrader:
    """
    服务降级策略，确保核心功能可用
    """
    def __init__(self, core_scenarios=None):
        self.core_scenarios = core_scenarios or ["read_webpage"]
        self.degraded = False
    
    def should_degrade(self, error_rate):
        """
        判断是否应该降级
        """
        if error_rate > 30:  # 错误率超过30%时降级
            self.degraded = True
            return True
        elif error_rate < 10:  # 错误率低于10%时恢复
            self.degraded = False
            return False
        return self.degraded
    
    def get_available_scenarios(self, scenarios):
        """
        获取可用的场景
        """
        if self.degraded:
            return [scenario for scenario in scenarios if scenario["name"] in self.core_scenarios]
        return scenarios

# 初始化重试机制、熔断机制和服务降级策略
retry_mechanism = RetryMechanism()
circuit_breaker = CircuitBreaker()
service_degrader = ServiceDegrader()

async def make_request(session, scenario):
    """发送单个请求并记录结果"""
    global error_count
    start_time = time.time()
    
    # 检查熔断状态
    if not circuit_breaker.is_allowed():
        end_time = time.time()
        response_time = end_time - start_time
        with lock:
            results.append({
                "scenario": scenario["name"],
                "status_code": 503,
                "response_time": response_time,
                "error": "Circuit breaker is open"
            })
            error_count += 1
        return
    
    async def send_request():
        async with session.post(f"{BASE_URL}{ENDPOINT}", json=scenario["payload"]) as response:
            return response.status, await response.text()
    
    try:
        # 使用重试机制
        status_code, _ = await retry_mechanism.execute(send_request)
        end_time = time.time()
        response_time = end_time - start_time
        
        with lock:
            results.append({
                "scenario": scenario["name"],
                "status_code": status_code,
                "response_time": response_time
            })
            if status_code == 200:
                circuit_breaker.record_success()
            else:
                circuit_breaker.record_failure()
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
            circuit_breaker.record_failure()

async def run_user(session, user_id):
    """模拟单个用户的请求"""
    for _ in range(REQUESTS_PER_USER):
        # 计算当前错误率
        current_error_rate = 0
        if results:
            current_error_count = len([r for r in results if r["status_code"] != 200])
            current_error_rate = current_error_count / len(results) * 100
        
        # 检查是否需要降级
        service_degrader.should_degrade(current_error_rate)
        
        # 获取可用的场景
        available_scenarios = service_degrader.get_available_scenarios(test_scenarios)
        
        # 随机选择一个测试场景
        scenario = available_scenarios[user_id % len(available_scenarios)]
        await make_request(session, scenario)
        # 随机等待时间
        await asyncio.sleep(0.5)

async def main():
    """主测试函数"""
    print("开始压力测试...")
    print(f"并发用户数: {CONCURRENT_USERS}")
    print(f"每个用户请求数: {REQUESTS_PER_USER}")
    print(f"总请求数: {TOTAL_REQUESTS}")
    print(f"测试场景: {[scenario['name'] for scenario in test_scenarios]}")
    print("=" * 80)
    
    start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(CONCURRENT_USERS):
            task = asyncio.create_task(run_user(session, i))
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
    with open("stress_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_requests": TOTAL_REQUESTS,
            "success_count": success_count,
            "error_count": error_count,
            "total_time": total_time,
            "average_response_time": statistics.mean(response_times),
            "95th_percentile": sorted(response_times)[int(len(response_times) * 0.95)],
            "99th_percentile": sorted(response_times)[int(len(response_times) * 0.99)],
            "throughput": TOTAL_REQUESTS / total_time,
            "results": results,
            "circuit_breaker_state": circuit_breaker.state,
            "service_degraded": service_degrader.degraded
        }, f, ensure_ascii=False, indent=2)
    
    # 显示熔断状态和服务降级状态
    print("\n系统状态:")
    print(f"熔断状态: {circuit_breaker.state}")
    print(f"服务降级: {'已降级' if service_degrader.degraded else '正常'}")
    print("\n测试结果已保存到 stress_test_results.json")

if __name__ == "__main__":
    asyncio.run(main())
