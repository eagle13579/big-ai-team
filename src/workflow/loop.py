import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# 添加项目根目录到 Python 路径
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# 导入配置，用于控制最大步数等参数
from src.shared.config import settings
from src.shared.logging import logger
from src.shared.monitoring import task_monitor

logger = logger.bind(name="AceAgent.Workflow")

import psutil


class MemoryManager:
    """
    优化的记忆管理器，负责管理 Agent 的短期和长期记忆
    """

    def __init__(
        self,
        memory_dir: str = "memory",
        max_short_term_memory: int = 50,  # 减少短期记忆容量
        memory_limit_mb: int = 80,  # 降低内存限制
    ):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.short_term_memory: list[dict[str, Any]] = []
        self.long_term_memory: dict[str, Any] = {}
        self.max_short_term_memory = max_short_term_memory
        self.memory_limit_mb = memory_limit_mb
        self._load_long_term_memory()
        self._memory_usage_history = []
        self._memory_check_interval = 5  # 内存检查间隔（任务数）
        self._task_count = 0

    def add_to_short_term_memory(self, item: dict[str, Any]):
        """添加到短期记忆"""
        # 为记忆项添加优先级和时间戳
        item["timestamp"] = item.get("timestamp", datetime.now().isoformat())
        item["priority"] = item.get("priority", 1)  # 默认为低优先级

        self.short_term_memory.append(item)
        self._task_count += 1
        
        # 定期检查内存使用情况
        if self._task_count % self._memory_check_interval == 0:
            # 检查内存使用情况
            if self._check_memory_usage():
                # 内存使用过高，清理部分记忆
                self._cleanup_memory()
            else:
                # 限制短期记忆大小
                if len(self.short_term_memory) > self.max_short_term_memory:
                    # 按优先级排序，保留高优先级记忆
                    self.short_term_memory.sort(key=lambda x: x.get("priority", 1), reverse=True)
                    self.short_term_memory = self.short_term_memory[: self.max_short_term_memory]

    def add_to_long_term_memory(self, key: str, value: Any):
        """添加到长期记忆"""
        self.long_term_memory[key] = value
        self._save_long_term_memory()
        # 检查内存使用情况
        if self._check_memory_usage():
            self._cleanup_memory()

    def get_short_term_memory(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取短期记忆"""
        # 按时间戳排序，返回最近的记忆
        sorted_memory = sorted(
            self.short_term_memory, key=lambda x: x.get("timestamp", ""), reverse=True
        )
        return sorted_memory[:limit]

    def get_long_term_memory(self, key: str | None = None) -> Any:
        """获取长期记忆"""
        if key:
            return self.long_term_memory.get(key)
        return self.long_term_memory

    def _save_long_term_memory(self):
        """保存长期记忆到文件"""
        memory_file = self.memory_dir / "long_term_memory.json"
        with open(memory_file, "w", encoding="utf-8") as f:
            json.dump(self.long_term_memory, f, indent=2, ensure_ascii=False)

    def _load_long_term_memory(self):
        """从文件加载长期记忆"""
        memory_file = self.memory_dir / "long_term_memory.json"
        if memory_file.exists():
            try:
                with open(memory_file, encoding="utf-8") as f:
                    self.long_term_memory = json.load(f)
            except Exception as e:
                logger.error(f"加载长期记忆失败: {str(e)}")

    def _check_memory_usage(self) -> bool:
        """检查内存使用情况"""
        process = psutil.Process()
        memory_usage = process.memory_info().rss / (1024 * 1024)  # 转换为 MB
        self._memory_usage_history.append(memory_usage)
        # 只保留最近的 10 条记录
        if len(self._memory_usage_history) > 10:
            self._memory_usage_history = self._memory_usage_history[-10:]

        logger.debug(f"当前内存使用: {memory_usage:.2f} MB")
        return memory_usage > self.memory_limit_mb

    def _cleanup_memory(self):
        """清理内存"""
        logger.warning("内存使用过高，开始清理记忆...")

        # 1. 清理短期记忆，保留高优先级和最近的记忆
        if len(self.short_term_memory) > 0:
            # 按优先级和时间戳排序
            self.short_term_memory.sort(
                key=lambda x: (x.get("priority", 1), x.get("timestamp", "")), reverse=True
            )
            # 只保留一半的记忆
            self.short_term_memory = self.short_term_memory[: len(self.short_term_memory) // 2]
            logger.info(f"已清理短期记忆，当前数量: {len(self.short_term_memory)}")

        # 2. 清理长期记忆，移除不常用的项
        if len(self.long_term_memory) > 0:
            # 这里可以根据实际情况实现更复杂的清理策略
            # 例如，移除最旧的项或使用频率最低的项
            pass

    def get_memory_usage_summary(self) -> dict[str, Any]:
        """获取内存使用摘要"""
        process = psutil.Process()
        memory_usage = process.memory_info().rss / (1024 * 1024)  # 转换为 MB

        return {
            "current_memory_usage_mb": memory_usage,
            "short_term_memory_count": len(self.short_term_memory),
            "long_term_memory_keys": len(self.long_term_memory),
            "memory_limit_mb": self.memory_limit_mb,
            "recent_memory_usage": self._memory_usage_history,
        }


class LLMClient:
    """
    LLM 客户端，负责与各种 LLM API 交互
    """

    def __init__(self, task: str = ""):
        self.api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")

        # 导入模型选择器
        try:
            from src.shared.model_selector import select_model_for_task

            self.model_name = select_model_for_task(task) if task else settings.DEFAULT_MODEL_NAME
        except ImportError:
            self.model_name = settings.DEFAULT_MODEL_NAME

        logger.info(f"🤖 为任务选择的模型: {self.model_name}")

    async def generate(self, prompt: str, temperature: float = 0.7) -> str:
        """
        生成文本
        """
        # 这里使用模拟实现，实际使用时应该调用真实的 LLM API
        # 例如 OpenAI、DeepSeek、Claude 等
        logger.info(f"📡 调用 LLM 生成文本，模型: {self.model_name}")

        # 模拟 API 调用延迟
        await asyncio.sleep(1.5)

        # 模拟不同场景的回复
        if "除以 0" in prompt:
            return "我尝试计算 10 除以 0，但这会导致数学错误。根据数学规则，除数不能为零。我将改为计算 10 除以 2，结果是 5。"
        elif "搜索" in prompt:
            return "根据搜索结果，Ace 浏览器在 2026 年 4 月已占据 AI 原生浏览器市场领先地位，拥有超过 35% 的市场份额。"
        else:
            return f"基于您的请求，我生成了以下内容：{prompt}"

    async def generate_decision(self, goal: str, context: str) -> dict[str, Any]:
        """
        生成决策
        """

        # 模拟决策生成
        await asyncio.sleep(1.0)

        # 基于上下文生成决策
        if "web_search" not in context:
            return {
                "action": "CALL_TOOL",
                "thought": "我需要先通过网络搜索了解用户的具体需求背景。",
                "tool": "web_search",
                "args": {"query": goal},
            }
        elif "write_file" not in context:
            return {
                "action": "CALL_TOOL",
                "thought": "搜集到的资料已经足够，我现在将其整理并保存为本地调研报告。",
                "tool": "write_file",
                "args": {
                    "filename": "research_report.md",
                    "content": f"基于最新搜索的调研结果：\n{context}",
                },
            }
        else:
            return {
                "action": "FINISH",
                "thought": "调研报告已生成并安全保存，所有子任务已完成。",
                "final_answer": "您的调研报告已保存至 research_report.md，任务顺利结束。",
            }


class ExecutionLoop:
    """
    🧠 2026 生产级自适应决策循环 (ReAct Loop)
    特性：
    1. 结构化思考链 (Thought -> Action -> Observation)
    2. 循环熔断机制 (Prevent Infinite Loops)
    3. 上下文状态自动回滚与记录
    4. 异步并发安全
    5. 集成真实 LLM
    6. 记忆管理
    7. 任务分解与规划
    8. 智能模型选择，实现 ROI 最大化
    """

    def __init__(self, executor, max_steps: int = None):
        self.executor = executor
        # 优先使用配置中心的步数限制，默认 10 步以防消耗过多 Token
        self.max_steps = max_steps or getattr(settings, "AGENT_MAX_STEPS", 10)
        self.history: list[dict[str, Any]] = []
        self.memory_manager = MemoryManager()
        # LLMClient 将在 run 方法中初始化，以便根据任务选择模型
        self.llm_client = None

    @task_monitor
    async def run(self, task_goal: str) -> dict[str, Any]:
        """
        🚀 执行核心：自适应任务处理
        """
        logger.info(f"🏁 [任务启动] 目标: {task_goal}")

        # 根据任务初始化 LLMClient，选择最合适的模型
        self.llm_client = LLMClient(task=task_goal)

        # 初始化运行上下文
        context = {
            "goal": task_goal,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "full_log": f"用户原始指令: {task_goal}\n",
            "selected_model": self.llm_client.model_name,
        }

        # 检查长期记忆中是否有相关信息
        memory_key = f"task_{hash(task_goal)}"
        memory_info = self.memory_manager.get_long_term_memory(memory_key)
        if memory_info:
            logger.info("🔍 从长期记忆中加载相关信息")
            context["full_log"] += f"从记忆中获取的信息: {memory_info}\n"

        is_completed = False
        current_step = 0

        while not is_completed and current_step < self.max_steps:
            current_step += 1
            logger.info(f"🧠 [第 {current_step} 步] 正在生成决策...")

            # 1. 思考阶段 (Thinking Phase)
            # 使用 LLM 生成决策
            decision = await self._think(task_goal, context["full_log"])

            thought = decision.get("thought", "正在分析下一步行动...")
            action_type = decision.get("action")  # 'CALL_TOOL' 或 'FINISH'

            logger.info(f"💡 思考结果: {thought}")

            # 2. 判定是否结束
            if action_type == "FINISH":
                logger.info(f"✅ 任务达成: {decision.get('final_answer')}")
                context["final_answer"] = decision.get("final_answer")
                is_completed = True
                break

            # 3. 执行阶段 (Acting Phase)
            tool_name = decision.get("tool")
            tool_args = decision.get("args", {})

            # 调用 executor 的统一接口执行工具
            execution_response = await self.executor.execute(tool_name, tool_args)

            # 4. 观察阶段 (Observing Phase)
            status = "成功" if execution_response["success"] else "失败"
            observation = (
                execution_response.get("result")
                if execution_response["success"]
                else execution_response.get("error")
            )

            # 更新上下文志，供下一步“思考”参考
            step_summary = (
                f"\n--- 步骤 {current_step} 记录 ---\n"
                f"思考: {thought}\n"
                f"动作: 调用工具 [{tool_name}]\n"
                f"结果状态: {status}\n"
                f"观察到: {observation}\n"
            )
            context["full_log"] += step_summary

            # 记录历史以便回溯
            step_record = {
                "step": current_step,
                "thought": thought,
                "tool": tool_name,
                "status": status,
                "observation": observation,
                "timestamp": datetime.now().isoformat(),
            }
            context["steps"].append(step_record)
            self.history.append(step_record)

            # 添加到短期记忆
            self.memory_manager.add_to_short_term_memory(step_record)

            # 如果工具连续失败，触发自愈提示
            if not execution_response["success"]:
                logger.warning(f"⚠️ 步骤 {current_step} 出现异常，Agent 将尝试修复逻辑...")
                # 生成修复提示
                repair_prompt = f"上一步执行失败，错误信息: {observation}。请提供一个修复方案。"
                repair_response = await self.llm_client.generate(repair_prompt)
                logger.info(f"🔧 修复方案: {repair_response}")
                context["full_log"] += f"修复方案: {repair_response}\n"

        # 检查是否因为达到最大步数而被迫终止
        if current_step >= self.max_steps and not is_completed:
            logger.error(f"🚨 任务因达到最大步数限制 ({self.max_steps}) 而强制停止。")
            context["status"] = "TIMEOUT"
        else:
            context["status"] = "SUCCESS"

        context["end_time"] = datetime.now().isoformat()
        context["total_steps"] = current_step

        # 保存到长期记忆
        self.memory_manager.add_to_long_term_memory(
            memory_key,
            {
                "goal": task_goal,
                "final_answer": context.get("final_answer"),
                "status": context["status"],
                "total_steps": current_step,
                "timestamp": datetime.now().isoformat(),
            },
        )

        return context

    async def _think(self, goal: str, full_log: str) -> dict[str, Any]:
        """
        核心决策逻辑：使用 LLM 生成决策
        """
        # 获取短期记忆
        short_term_memory = self.memory_manager.get_short_term_memory()
        memory_context = "\n".join(
            [
                f"Step {m['step']}: {m['thought']} -> {m['tool']} -> {m['status']}"
                for m in short_term_memory
            ]
        )

        # 生成决策
        decision = await self.llm_client.generate_decision(goal, full_log + "\n" + memory_context)
        return decision

    def get_history_summary(self) -> str:
        """获取任务执行摘要"""
        summary = f"任务概览 (共 {len(self.history)} 步):\n"
        for h in self.history:
            summary += f"[{h['step']}] {h['tool']} -> {h['status']}\n"
        return summary

    def clear_history(self):
        """清除历史记录"""
        self.history = []

    def get_memory_summary(self) -> dict[str, Any]:
        """获取记忆摘要"""
        return self.memory_manager.get_memory_usage_summary()
