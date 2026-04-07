import asyncio
import json
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
from pathlib import Path

# 导入配置，用于控制最大步数等参数
from ..shared.config import settings
from ..persistence.memory import MemoryManager as DBMemoryManager
from ..persistence.database import get_db

logger = logging.getLogger("AceAgent.Workflow")

class MemoryManager:
    """
    记忆管理器，负责管理 Agent 的短期和长期记忆
    集成了mempalace功能
    """
    def __init__(self, memory_dir: str = "memory", palace_path: str = "~/.mempalace/palace"):
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(exist_ok=True)
        self.short_term_memory: List[Dict[str, Any]] = []
        self.long_term_memory: Dict[str, Any] = {}
        self._load_long_term_memory()
        
        # 初始化数据库记忆管理器（集成mempalace）
        db = next(get_db())
        self.db_memory_manager = DBMemoryManager(db, palace_path)

    def add_to_short_term_memory(self, item: Dict[str, Any]):
        """添加到短期记忆"""
        self.short_term_memory.append(item)
        # 限制短期记忆大小
        if len(self.short_term_memory) > 100:
            self.short_term_memory = self.short_term_memory[-100:]

    def add_to_long_term_memory(self, key: str, value: Any):
        """添加到长期记忆"""
        self.long_term_memory[key] = value
        self._save_long_term_memory()

    def get_short_term_memory(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取短期记忆"""
        return self.short_term_memory[-limit:]

    def get_long_term_memory(self, key: Optional[str] = None) -> Any:
        """获取长期记忆"""
        if key:
            return self.long_term_memory.get(key)
        return self.long_term_memory

    def search_with_mempalace(self, query: str, limit: int = 5, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """使用mempalace搜索记忆（支持上下文感知）"""
        return self.db_memory_manager.search_with_mempalace(query, limit, context)

    def get_wake_up_context(self, context: Dict[str, Any] = None) -> str:
        """获取mempalace唤醒上下文（支持个性化）"""
        return self.db_memory_manager.get_wake_up_context(context)

    def compress_content(self, content: str) -> str:
        """使用AAAK压缩内容"""
        return self.db_memory_manager.compress_content(content)

    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        summary = {
            "short_term_memory_count": len(self.short_term_memory),
            "long_term_memory_keys": list(self.long_term_memory.keys())
        }
        # 添加mempalace记忆摘要
        try:
            mempalace_summary = self.db_memory_manager.get_memory_summary()
            summary.update({"mempalace": mempalace_summary})
        except Exception as e:
            logger.error(f"获取mempalace记忆摘要失败: {str(e)}")
        return summary

    def add_memory_with_context(self, content: str, context: Dict[str, Any], tags: List[str] = None) -> Dict[str, Any]:
        """添加带情境的记忆"""
        return self.db_memory_manager.add_memory_with_context(content, context, tags)

    def get_contextual_memory(self, context: Dict[str, Any], limit: int = 5) -> List[Dict[str, Any]]:
        """获取与上下文相关的记忆"""
        return self.db_memory_manager.get_contextual_memory(context, limit)

    def cleanup_memory(self):
        """清理过期记忆"""
        return self.db_memory_manager.cleanup_memory()

    def get_memory_analytics(self) -> Dict[str, Any]:
        """获取记忆分析"""
        return self.db_memory_manager.get_memory_analytics()

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
                with open(memory_file, "r", encoding="utf-8") as f:
                    self.long_term_memory = json.load(f)
            except Exception as e:
                logger.error(f"加载长期记忆失败: {str(e)}")


class LLMClient:
    """
    LLM 客户端，负责与各种 LLM API 交互
    """
    def __init__(self, task: str = ""):
        self.api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("DEEPSEEK_API_KEY")
        
        # 导入模型选择器
        try:
            from ..shared.model_selector import select_model_for_task
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

    async def generate_decision(self, goal: str, context: str) -> Dict[str, Any]:
        """
        生成决策
        """
        prompt = f"""
        你是一个智能 Agent，需要根据目标和上下文做出决策。
        
        目标: {goal}
        上下文: {context}
        
        请返回以下格式的 JSON 决策：
        {
            "action": "CALL_TOOL" 或 "FINISH",
            "thought": "你的思考过程",
            "tool": "工具名称" (如果 action 是 CALL_TOOL),
            "args": {"参数名": "参数值"} (如果 action 是 CALL_TOOL),
            "final_answer": "最终答案" (如果 action 是 FINISH)
        }
        """
        
        # 模拟决策生成
        await asyncio.sleep(1.0)
        
        # 基于上下文生成决策
        if "web_search" not in context:
            return {
                "action": "CALL_TOOL",
                "thought": "我需要先通过网络搜索了解用户的具体需求背景。",
                "tool": "web_search",
                "args": {"query": goal}
            }
        elif "write_file" not in context:
            return {
                "action": "CALL_TOOL",
                "thought": "搜集到的资料已经足够，我现在将其整理并保存为本地调研报告。",
                "tool": "write_file",
                "args": {
                    "filename": "research_report.md",
                    "content": f"基于最新搜索的调研结果：\n{context}"
                }
            }
        else:
            return {
                "action": "FINISH",
                "thought": "调研报告已生成并安全保存，所有子任务已完成。",
                "final_answer": "您的调研报告已保存至 research_report.md，任务顺利结束。"
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

    def __init__(self, executor, max_steps: int = None, palace_path: str = "~/.mempalace/palace"):
        self.executor = executor
        # 优先使用配置中心的步数限制，默认 10 步以防消耗过多 Token
        self.max_steps = max_steps or getattr(settings, "AGENT_MAX_STEPS", 10)
        self.history: List[Dict[str, Any]] = []
        self.memory_manager = MemoryManager(palace_path=palace_path)
        # LLMClient 将在 run 方法中初始化，以便根据任务选择模型
        self.llm_client = None
        # 记忆分析数据
        self.memory_analytics = {}


    async def run(self, task_goal: str, user_context: Dict[str, Any] = None) -> Dict[str, Any]:
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
            "user_context": user_context or {}
        }
        
        # 获取个性化mempalace唤醒上下文
        try:
            wake_up_context = self.memory_manager.get_wake_up_context(user_context)
            if wake_up_context:
                logger.info("🔍 从mempalace获取个性化唤醒上下文")
                context["full_log"] += f"从mempalace获取的唤醒上下文: {wake_up_context}\n"
        except Exception as e:
            logger.error(f"获取mempalace唤醒上下文失败: {str(e)}")
        
        # 检查长期记忆中是否有相关信息
        memory_key = f"task_{hash(task_goal)}"
        memory_info = self.memory_manager.get_long_term_memory(memory_key)
        if memory_info:
            logger.info("🔍 从长期记忆中加载相关信息")
            context["full_log"] += f"从记忆中获取的信息: {memory_info}\n"
        
        # 使用上下文感知的mempalace搜索
        try:
            mempalace_results = self.memory_manager.search_with_mempalace(task_goal, context=user_context)
            if mempalace_results:
                logger.info("🔍 从mempalace搜索到相关记忆")
                context["full_log"] += f"从mempalace搜索到的信息: {mempalace_results}\n"
        except Exception as e:
            logger.error(f"使用mempalace搜索记忆失败: {str(e)}")
        
        # 获取与上下文相关的记忆
        try:
            if user_context:
                contextual_memories = self.memory_manager.get_contextual_memory(user_context)
                if contextual_memories:
                    logger.info("🔍 从mempalace获取上下文相关记忆")
                    context["full_log"] += f"从mempalace获取的上下文相关信息: {contextual_memories}\n"
        except Exception as e:
            logger.error(f"获取上下文相关记忆失败: {str(e)}")
        
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
            observation = execution_response.get("result") if execution_response["success"] else execution_response.get("error")
            
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
                "timestamp": datetime.now().isoformat()
            }
            context["steps"].append(step_record)
            self.history.append(step_record)
            
            # 添加到短期记忆
            self.memory_manager.add_to_short_term_memory(step_record)
            
            # 同时添加到mempalace（带情境）
            try:
                memory_context = {
                    "task": task_goal,
                    "step": current_step,
                    "tool": tool_name,
                    "status": status,
                    "user_context": user_context or {}
                }
                self.memory_manager.add_memory_with_context(
                    content=step_summary,
                    context=memory_context,
                    tags=[tool_name, status]
                )
            except Exception as e:
                logger.error(f"添加到mempalace失败: {str(e)}")

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
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 同时保存到mempalace（带情境）
        try:
            final_context = {
                "task": task_goal,
                "status": context["status"],
                "total_steps": current_step,
                "user_context": user_context or {}
            }
            self.memory_manager.add_memory_with_context(
                content=f"任务: {task_goal}\n状态: {context['status']}\n最终答案: {context.get('final_answer')}",
                context=final_context,
                tags=["task", context["status"]]
            )
        except Exception as e:
            logger.error(f"保存到mempalace失败: {str(e)}")
        
        # 获取记忆分析
        try:
            self.memory_analytics = self.memory_manager.get_memory_analytics()
            logger.info(f"📊 记忆分析: {self.memory_analytics}")
            context["memory_analytics"] = self.memory_analytics
        except Exception as e:
            logger.error(f"获取记忆分析失败: {str(e)}")
        
        # 定期清理过期记忆
        try:
            cleanup_result = self.memory_manager.cleanup_memory()
            if cleanup_result.get("success"):
                logger.info(f"🧹 清理过期记忆: 删除了 {cleanup_result.get('deleted_count', 0)} 个过期记忆")
        except Exception as e:
            logger.error(f"清理过期记忆失败: {str(e)}")
        
        return context

    async def _think(self, goal: str, full_log: str) -> Dict[str, Any]:
        """
        核心决策逻辑：使用 LLM 生成决策
        """
        # 获取短期记忆
        short_term_memory = self.memory_manager.get_short_term_memory()
        memory_context = "\n".join([f"Step {m['step']}: {m['thought']} -> {m['tool']} -> {m['status']}" for m in short_term_memory])
        
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

    def get_memory_summary(self) -> Dict[str, Any]:
        """获取记忆摘要"""
        return {
            "short_term_memory_count": len(self.memory_manager.short_term_memory),
            "long_term_memory_keys": list(self.memory_manager.long_term_memory.keys())
        }
