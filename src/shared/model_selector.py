import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

try:
    from .model_policy_tracker import CostEstimate, policy_tracker

    POLICY_TRACKER_AVAILABLE = True
except ImportError:
    POLICY_TRACKER_AVAILABLE = False

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""

    TEXT_GENERATION = "text_generation"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"
    ANALYSIS = "analysis"
    SEARCH = "search"
    SUMMARY = "summary"
    TRANSLATION = "translation"
    CREATIVE_WRITING = "creative_writing"


class ComplexityLevel(Enum):
    """复杂度等级枚举"""

    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


@dataclass
class ModelInfo:
    """模型信息"""

    name: str
    provider: str
    cost_per_1k_tokens: float
    capabilities: list[str]
    max_tokens: int
    recommended_for: list[TaskType]


class ModelSelector:
    """
    智能模型选择器，根据任务类型、复杂度和预算选择最合适的模型
    实现 ROI 最大化
    """

    def __init__(self):
        # 模型配置
        self.models = {
            # 免费/开源模型（ROI 王者！）
            "ollama-llama3": ModelInfo(
                name="ollama-llama3",
                provider="ollama",
                cost_per_1k_tokens=0.0,  # 完全免费！本地运行
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                    "summary",
                ],
                max_tokens=8192,
                recommended_for=[
                    TaskType.TEXT_GENERATION,
                    TaskType.ANALYSIS,
                    TaskType.SUMMARY,
                    TaskType.CODE_GENERATION,
                ],
            ),
            "ollama-qwen2.5": ModelInfo(
                name="ollama-qwen2.5",
                provider="ollama",
                cost_per_1k_tokens=0.0,  # 完全免费！本地运行
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                    "translation",
                    "creative_writing",
                ],
                max_tokens=128000,
                recommended_for=[
                    TaskType.TEXT_GENERATION,
                    TaskType.ANALYSIS,
                    TaskType.REASONING,
                    TaskType.CODE_GENERATION,
                    TaskType.TRANSLATION,
                ],
            ),
            "ollama-mistral": ModelInfo(
                name="ollama-mistral",
                provider="ollama",
                cost_per_1k_tokens=0.0,  # 完全免费！本地运行
                capabilities=["text_generation", "analysis", "code_generation", "summary"],
                max_tokens=32768,
                recommended_for=[
                    TaskType.TEXT_GENERATION,
                    TaskType.ANALYSIS,
                    TaskType.CODE_GENERATION,
                    TaskType.SUMMARY,
                ],
            ),
            # 低成本模型
            "deepseek-chat": ModelInfo(
                name="deepseek-chat",
                provider="deepseek",
                cost_per_1k_tokens=0.00014,  # $0.14 每百万 token
                capabilities=["text_generation", "analysis", "summary", "translation"],
                max_tokens=128000,
                recommended_for=[
                    TaskType.TEXT_GENERATION,
                    TaskType.ANALYSIS,
                    TaskType.SUMMARY,
                    TaskType.TRANSLATION,
                ],
            ),
            "gpt-3.5-turbo": ModelInfo(
                name="gpt-3.5-turbo",
                provider="openai",
                cost_per_1k_tokens=0.0015,  # $1.5 每百万 token
                capabilities=["text_generation", "analysis", "summary", "translation"],
                max_tokens=16384,
                recommended_for=[
                    TaskType.TEXT_GENERATION,
                    TaskType.ANALYSIS,
                    TaskType.SUMMARY,
                    TaskType.TRANSLATION,
                ],
            ),
            # 中等成本模型
            "claude-3-5-sonnet-latest": ModelInfo(
                name="claude-3-5-sonnet-latest",
                provider="anthropic",
                cost_per_1k_tokens=0.003,  # $3 每百万 token
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "creative_writing",
                    "summary",
                ],
                max_tokens=200000,
                recommended_for=[
                    TaskType.ANALYSIS,
                    TaskType.REASONING,
                    TaskType.CREATIVE_WRITING,
                    TaskType.SUMMARY,
                ],
            ),
            "gpt-4o-mini": ModelInfo(
                name="gpt-4o-mini",
                provider="openai",
                cost_per_1k_tokens=0.0015,  # $1.5 每百万 token
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                    "summary",
                ],
                max_tokens=128000,
                recommended_for=[
                    TaskType.ANALYSIS,
                    TaskType.REASONING,
                    TaskType.CODE_GENERATION,
                    TaskType.SUMMARY,
                ],
            ),
            # 高成本模型
            "gpt-4o-2026": ModelInfo(
                name="gpt-4o-2026",
                provider="openai",
                cost_per_1k_tokens=0.005,  # $5 每百万 token
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                    "creative_writing",
                    "search",
                ],
                max_tokens=128000,
                recommended_for=[
                    TaskType.REASONING,
                    TaskType.CODE_GENERATION,
                    TaskType.CREATIVE_WRITING,
                    TaskType.SEARCH,
                ],
            ),
            "gemini-1.5-pro": ModelInfo(
                name="gemini-1.5-pro",
                provider="google",
                cost_per_1k_tokens=0.0035,  # $3.5 每百万 token
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                    "creative_writing",
                    "multimodal",
                ],
                max_tokens=1000000,
                recommended_for=[
                    TaskType.REASONING,
                    TaskType.CODE_GENERATION,
                    TaskType.CREATIVE_WRITING,
                ],
            ),
            # 长文本专家
            "moonshot-v1-128k": ModelInfo(
                name="moonshot-v1-128k",
                provider="moonshot",
                cost_per_1k_tokens=0.0012,  # $1.2 每百万 token
                capabilities=["text_generation", "analysis", "summary"],
                max_tokens=128000,
                recommended_for=[TaskType.SUMMARY, TaskType.ANALYSIS, TaskType.TEXT_GENERATION],
            ),
            "glm-4": ModelInfo(
                name="glm-4",
                provider="zhipu",
                cost_per_1k_tokens=0.001,  # $1 每百万 token
                capabilities=["text_generation", "analysis", "reasoning", "code_generation"],
                max_tokens=128000,
                recommended_for=[
                    TaskType.TEXT_GENERATION,
                    TaskType.ANALYSIS,
                    TaskType.REASONING,
                    TaskType.CODE_GENERATION,
                ],
            ),
            "glm-4-flash": ModelInfo(
                name="glm-4-flash",
                provider="zhipu",
                cost_per_1k_tokens=0.0,  # 完全免费！
                capabilities=[
                    "text_generation",
                    "analysis",
                    "reasoning",
                    "code_generation",
                    "translation",
                    "creative_writing",
                ],
                max_tokens=128000,
                recommended_for=[
                    TaskType.TEXT_GENERATION,
                    TaskType.ANALYSIS,
                    TaskType.REASONING,
                    TaskType.CODE_GENERATION,
                    TaskType.TRANSLATION,
                    TaskType.CREATIVE_WRITING,
                ],
            ),
        }

        # 任务类型检测规则
        self.task_type_rules = {
            "代码": TaskType.CODE_GENERATION,
            "编程": TaskType.CODE_GENERATION,
            "开发": TaskType.CODE_GENERATION,
            "实现": TaskType.CODE_GENERATION,
            "分析": TaskType.ANALYSIS,
            "研究": TaskType.ANALYSIS,
            "调研": TaskType.ANALYSIS,
            "推理": TaskType.REASONING,
            "计算": TaskType.REASONING,
            "搜索": TaskType.SEARCH,
            "查找": TaskType.SEARCH,
            "总结": TaskType.SUMMARY,
            "摘要": TaskType.SUMMARY,
            "翻译": TaskType.TRANSLATION,
            "创作": TaskType.CREATIVE_WRITING,
            "写作": TaskType.CREATIVE_WRITING,
        }

    def detect_task_type(self, task: str) -> TaskType:
        """
        检测任务类型
        """
        task_lower = task.lower()

        for keyword, task_type in self.task_type_rules.items():
            if keyword in task_lower:
                return task_type

        # 默认返回文本生成
        return TaskType.TEXT_GENERATION

    def estimate_complexity(self, task: str) -> ComplexityLevel:
        """
        估算任务复杂度
        """
        # 基于任务长度估算复杂度
        task_length = len(task)

        if task_length < 50:
            return ComplexityLevel.SIMPLE
        elif task_length < 200:
            return ComplexityLevel.MEDIUM
        elif task_length < 500:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX

    def select_model(
        self,
        task: str,
        budget: float | None = None,
        preferred_models: list[str] | None = None,
        prefer_free: bool = True,
        estimated_input_tokens: int = 1000,
        estimated_output_tokens: int = 500,
        warn_before_pay: bool = True,
    ) -> ModelInfo:
        """
        选择最合适的模型
        """
        # 检测任务类型和复杂度
        task_type = self.detect_task_type(task)
        complexity = self.estimate_complexity(task)

        # 如果有政策追踪器，先获取最新政策
        if POLICY_TRACKER_AVAILABLE:
            logger.info("📋 使用最新模型政策数据")

        # 过滤适合的模型
        suitable_models = []

        for model_info in self.models.values():
            # 检查模型是否推荐用于该任务类型
            if (
                task_type in model_info.recommended_for
                or task_type.value in model_info.capabilities
            ):
                # 检查预算限制
                if budget is None or model_info.cost_per_1k_tokens <= budget:
                    suitable_models.append(model_info)

        # 如果没有合适的模型，放宽条件
        if not suitable_models:
            suitable_models = list(self.models.values())

        # 模型质量评估
        def evaluate_model_quality(
            model: ModelInfo, task_type: TaskType, complexity: ComplexityLevel
        ) -> float:
            """
            评估模型质量，确保免费模型能满足任务需求
            返回 0-1 之间的质量分数，1 表示最高质量
            """
            quality_score = 0.0

            # 基础质量分数
            if model.cost_per_1k_tokens == 0.0:
                # 免费模型的基础分数
                if "ollama" in model.name:
                    # Ollama 本地模型质量
                    if "llama3" in model.name:
                        quality_score = 0.85  # Llama 3 质量较高
                    elif "qwen2.5" in model.name:
                        quality_score = 0.88  # Qwen 2.5 中文优化
                    elif "mistral" in model.name:
                        quality_score = 0.82  # Mistral 质量不错
                elif model.name == "glm-4-flash":
                    quality_score = 0.90  # GLM-4-Flash 质量很高
            else:
                # 付费模型的基础分数
                if model.name in ["gpt-4o", "gpt-4o-2026"]:
                    quality_score = 0.99  # GPT-4 质量最高
                elif model.name in ["claude-3-5-sonnet"]:
                    quality_score = 0.98  # Claude 3.5 质量很高
                elif model.name in ["gemini-1.5-pro"]:
                    quality_score = 0.97  # Gemini 1.5 质量很高
                elif model.name in ["deepseek-chat", "deepseek-coder"]:
                    quality_score = 0.92  # DeepSeek 质量不错
                elif model.name in ["gpt-3.5-turbo", "gpt-4o-mini"]:
                    quality_score = 0.90  # GPT-3.5 质量不错
                elif model.name in ["glm-4"]:
                    quality_score = 0.91  # GLM-4 质量不错

            # 根据任务类型调整分数
            if task_type == TaskType.CODE_GENERATION:
                if "code_generation" in model.capabilities:
                    quality_score += 0.1
            elif task_type == TaskType.REASONING:
                if "reasoning" in model.capabilities:
                    quality_score += 0.1
            elif task_type == TaskType.SEARCH:
                if "search" in model.capabilities:
                    quality_score = 1.0  # 搜索任务需要特定能力
            elif task_type == TaskType.CREATIVE_WRITING:
                if "creative_writing" in model.capabilities:
                    quality_score += 0.05

            # 根据复杂度调整分数
            if complexity == ComplexityLevel.VERY_COMPLEX:
                # 非常复杂的任务需要更高质量的模型
                if model.cost_per_1k_tokens == 0.0:
                    # 免费模型处理非常复杂任务的能力有限
                    quality_score *= 0.8

            return min(quality_score, 1.0)  # 确保分数不超过 1.0

        # 综合评分函数
        def comprehensive_score(model: ModelInfo) -> float:
            """
            综合考虑成本和质量的评分函数
            分数越低越好（优先选择）
            """
            # 计算质量分数
            quality_score = evaluate_model_quality(model, task_type, complexity)

            # 计算成本分数
            cost_score = model.cost_per_1k_tokens

            # 质量阈值检查
            min_quality_threshold = 0.7
            if quality_score < min_quality_threshold:
                # 质量太低，不考虑
                return float("inf")

            # 免费模型的特殊处理
            if prefer_free and model.cost_per_1k_tokens == 0.0:
                # 免费模型且质量足够，给予超级优先
                if quality_score >= 0.8:
                    return -1000.0 + (1.0 - quality_score) * 100  # 质量越高排名越前

            # 综合评分：成本 + 质量惩罚
            # 质量越高，成本惩罚越小
            quality_penalty = (1.0 - quality_score) * 0.1  # 质量差的模型需要更高的成本惩罚
            total_score = cost_score + quality_penalty

            # 对于复杂任务，调整评分
            if complexity in [ComplexityLevel.COMPLEX, ComplexityLevel.VERY_COMPLEX]:
                # 复杂任务更重视质量
                if "reasoning" in model.capabilities or "code_generation" in model.capabilities:
                    total_score *= 0.8

            return total_score

        # 排序并选择最佳模型
        suitable_models.sort(key=comprehensive_score)

        # 如果有偏好模型，优先选择
        if preferred_models:
            for preferred_model in preferred_models:
                for model in suitable_models:
                    if model.name == preferred_model:
                        return model

        # 选择最佳模型
        selected_model = suitable_models[0]

        # 成本预估和警告
        if POLICY_TRACKER_AVAILABLE and warn_before_pay:
            estimate = policy_tracker.estimate_cost(
                selected_model.name, estimated_input_tokens, estimated_output_tokens
            )

            if not estimate.is_free:
                logger.warning(
                    f"💰 成本预估: 使用 {selected_model.name} 约需 ${estimate.estimated_cost:.4f}"
                )
                if estimate.warning:
                    logger.warning(estimate.warning)

            if estimate.is_free:
                logger.info(f"🆓 免费模型: {selected_model.name} ({estimate.free_quota_remaining})")

        return selected_model

    def get_cost_estimate(
        self,
        model_name: str,
        estimated_input_tokens: int = 1000,
        estimated_output_tokens: int = 500,
    ) -> CostEstimate | None:
        """
        获取成本预估
        """
        if POLICY_TRACKER_AVAILABLE:
            return policy_tracker.estimate_cost(
                model_name, estimated_input_tokens, estimated_output_tokens
            )
        return None

    def should_ask_user_before_execution(
        self,
        model_name: str,
        estimated_input_tokens: int = 1000,
        estimated_output_tokens: int = 500,
    ) -> bool:
        """
        判断执行前是否需要询问用户
        """
        if POLICY_TRACKER_AVAILABLE:
            return policy_tracker.should_ask_user(
                model_name, estimated_input_tokens, estimated_output_tokens
            )
        return False

    def get_roi_report(self) -> dict[str, Any] | None:
        """
        获取 ROI 报告
        """
        if POLICY_TRACKER_AVAILABLE:
            return policy_tracker.get_roi_report()
        return None

    def get_model_info(self, model_name: str) -> ModelInfo | None:
        """
        获取指定模型的信息
        """
        return self.models.get(model_name)

    def list_available_models(self) -> list[ModelInfo]:
        """
        列出所有可用模型
        """
        return list(self.models.values())


# 全局模型选择器实例
model_selector = ModelSelector()


def select_model_for_task(
    task: str,
    budget: float | None = None,
    preferred_models: list[str] | None = None,
    prefer_free: bool = True,
) -> str:
    """
    为任务选择合适的模型
    这是一个简化的接口，返回模型名称
    """
    selected_model = model_selector.select_model(task, budget, preferred_models, prefer_free)
    return selected_model.name
