#!/usr/bin/env python3
"""
部署前自动化测试脚本
用于在部署前验证系统的各个组件是否正常工作
"""

import os
import sys
import subprocess
import time
import json
from typing import Dict, List, Optional

class PreDeployTester:
    def __init__(self):
        self.test_results = []
        self.success = True
    
    def run_test(self, test_name: str, test_func) -> bool:
        """运行单个测试"""
        print(f"\n=== 运行测试: {test_name} ===")
        start_time = time.time()
        try:
            result = test_func()
            duration = time.time() - start_time
            if result:
                print(f"✅ {test_name} 测试通过! (耗时: {duration:.2f}s)")
                self.test_results.append({
                    "name": test_name,
                    "status": "pass",
                    "duration": duration
                })
                return True
            else:
                print(f"❌ {test_name} 测试失败!")
                self.test_results.append({
                    "name": test_name,
                    "status": "fail",
                    "duration": duration
                })
                self.success = False
                return False
        except Exception as e:
            duration = time.time() - start_time
            print(f"❌ {test_name} 测试出错: {str(e)}")
            self.test_results.append({
                "name": test_name,
                "status": "error",
                "duration": duration,
                "error": str(e)
            })
            self.success = False
            return False
    
    def test_unit_tests(self) -> bool:
        """运行单元测试"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/unit/", "-v"],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"运行单元测试时出错: {str(e)}")
            return False
    
    def test_integration_tests(self) -> bool:
        """运行集成测试"""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/integration/", "-v"],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"运行集成测试时出错: {str(e)}")
            return False
    
    def test_frontend_build(self) -> bool:
        """测试前端构建"""
        if not os.path.exists("frontend"):
            print("前端目录不存在，跳过前端构建测试")
            return True
        
        try:
            # 检查是否安装了 npm
            npm_check = subprocess.run(["npm", "--version"], capture_output=True)
            if npm_check.returncode != 0:
                print("npm 未安装，跳过前端构建测试")
                return True
            
            # 运行前端测试
            result = subprocess.run(
                ["npm", "test", "--", "--watchAll=false"],
                cwd="frontend",
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)
            
            # 运行前端构建
            build_result = subprocess.run(
                ["npm", "run", "build"],
                cwd="frontend",
                capture_output=True,
                text=True
            )
            print(build_result.stdout)
            if build_result.stderr:
                print("错误输出:", build_result.stderr)
            
            return result.returncode == 0 and build_result.returncode == 0
        except Exception as e:
            print(f"测试前端构建时出错: {str(e)}")
            return False
    
    def test_docker_build(self) -> bool:
        """测试 Docker 构建"""
        try:
            # 检查 Docker 是否运行
            docker_check = subprocess.run(["docker", "version"], capture_output=True)
            if docker_check.returncode != 0:
                print("Docker 未运行，跳过 Docker 构建测试")
                return True
            
            # 构建 Docker 镜像
            result = subprocess.run(
                ["docker", "build", "-t", "big-ai-app:test", "."],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            if result.stderr:
                print("错误输出:", result.stderr)
            return result.returncode == 0
        except Exception as e:
            print(f"测试 Docker 构建时出错: {str(e)}")
            return False
    
    def test_security_audit(self) -> bool:
        """运行安全审计"""
        try:
            # 检查是否存在安全审计脚本
            if os.path.exists("scripts/tools/security_audit.py"):
                result = subprocess.run(
                    [sys.executable, "scripts/tools/security_audit.py"],
                    capture_output=True,
                    text=True
                )
                print(result.stdout)
                if result.stderr:
                    print("错误输出:", result.stderr)
                return result.returncode == 0
            else:
                print("安全审计脚本不存在，跳过安全审计测试")
                return True
        except Exception as e:
            print(f"运行安全审计时出错: {str(e)}")
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=========================================")
        print("🚀 部署前自动化测试")
        print("=========================================")
        
        # 运行测试
        self.run_test("单元测试", self.test_unit_tests)
        self.run_test("集成测试", self.test_integration_tests)
        self.run_test("前端构建", self.test_frontend_build)
        self.run_test("Docker 构建", self.test_docker_build)
        self.run_test("安全审计", self.test_security_audit)
        
        # 生成测试报告
        self.generate_report()
        
        # 输出最终结果
        print("\n=========================================")
        if self.success:
            print("🎉 所有测试通过！可以进行部署。")
        else:
            print("❌ 部分测试失败，部署前请修复这些问题。")
        print("=========================================")
        
        return self.success
    
    def generate_report(self):
        """生成测试报告"""
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "results": self.test_results,
            "success": self.success
        }
        
        # 保存报告到文件
        with open("pre_deploy_test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 测试报告已保存到: pre_deploy_test_report.json")
        
        # 打印摘要
        print("\n测试摘要:")
        for test in self.test_results:
            status = "✅" if test["status"] == "pass" else "❌"
            print(f"{status} {test['name']}: {test['status']} (耗时: {test['duration']:.2f}s)")

if __name__ == "__main__":
    tester = PreDeployTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)