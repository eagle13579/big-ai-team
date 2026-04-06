import os
import json
import asyncio
import aiohttp
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelPolicy:
    """模型政策信息"""
    model_name: str
    provider: str
    is_free: bool
    free_quota: Optional[str] = None  # 免费额度描述
    free_limit: Optional[int] = None    # 免费 token 限制
    cost_per_1k_tokens_input: float = 0.0
    cost_per_1k_tokens_output: float = 0.0
    last_updated: str = ""
    source_url: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class CostEstimate:
    """成本预估"""
    model_name: str
    estimated_input_tokens: int
    estimated_output_tokens: int
    estimated_cost: float
    is_free: bool
    free_quota_remaining: Optional[str] = None
    warning: Optional[str] = None


class ModelPolicyTracker:
    """
    模型政策追踪器
    实时追踪主流模型的免费政策和定价
    """
    
    def __init__(self, cache_file: str = "model_policies_cache.json"):
        self.cache_file = cache_file
        self.policies: Dict[str, ModelPolicy] = {}
        self.last_updated: Optional[datetime] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # 初始化默认模型政策
        self._init_default_policies()
        
        # 尝试从缓存加载
        self._load_from_cache()
    
    def _init_default_policies(self):
        """初始化默认模型政策"""
        default_policies = [
            # DeepSeek 系列（国内）
            ModelPolicy(
                model_name="deepseek-chat",
                provider="deepseek",
                is_free=False,
                free_quota="新用户注册送额度",
                cost_per_1k_tokens_input=0.00014,
                cost_per_1k_tokens_output=0.00028,
                notes="DeepSeek 性价比很高，有时有免费活动",
                source_url="https://platform.deepseek.com/"
            ),
            ModelPolicy(
                model_name="deepseek-coder",
                provider="deepseek",
                is_free=False,
                cost_per_1k_tokens_input=0.00014,
                cost_per_1k_tokens_output=0.00028,
                notes="代码专用模型",
                source_url="https://platform.deepseek.com/"
            ),
            
            # 智谱 AI（国内）
            ModelPolicy(
                model_name="glm-4",
                provider="zhipu",
                is_free=False,
                free_quota="新用户注册送额度",
                cost_per_1k_tokens_input=0.001,
                cost_per_1k_tokens_output=0.001,
                notes="智谱 AI，中文优化",
                source_url="https://open.bigmodel.cn/"
            ),
            ModelPolicy(
                model_name="glm-4-flash",
                provider="zhipu",
                is_free=True,
                free_quota="永久免费，不限量",
                notes="GLM-4-Flash 完全免费！",
                source_url="https://open.bigmodel.cn/"
            ),
            
            # 月之暗面（国内）
            ModelPolicy(
                model_name="moonshot-v1-128k",
                provider="moonshot",
                is_free=False,
                free_quota="新用户注册送额度",
                cost_per_1k_tokens_input=0.0012,
                cost_per_1k_tokens_output=0.0012,
                notes="长文本处理",
                source_url="https://platform.moonshot.cn/"
            ),
            
            # 零一万物（国内）
            ModelPolicy(
                model_name="yi-large",
                provider="lingyi",
                is_free=False,
                free_quota="新用户注册送额度",
                cost_per_1k_tokens_input=0.002,
                cost_per_1k_tokens_output=0.002,
                source_url="https://platform.lingyiwanwu.com/"
            ),
            
            # 字节跳动豆包（国内）
            ModelPolicy(
                model_name="doubao-pro",
                provider="doubao",
                is_free=False,
                free_quota="新用户注册送额度",
                cost_per_1k_tokens_input=0.003,
                cost_per_1k_tokens_output=0.003,
                source_url="https://console.volcengine.com/ark/"
            ),
            
            # OpenAI 系列
            ModelPolicy(
                model_name="gpt-4o-mini",
                provider="openai",
                is_free=False,
                free_quota="新用户注册送 $5-18 额度",
                cost_per_1k_tokens_input=0.0015,
                cost_per_1k_tokens_output=0.006,
                source_url="https://openai.com/pricing"
            ),
            ModelPolicy(
                model_name="gpt-4o",
                provider="openai",
                is_free=False,
                cost_per_1k_tokens_input=0.005,
                cost_per_1k_tokens_output=0.015,
                source_url="https://openai.com/pricing"
            ),
            ModelPolicy(
                model_name="gpt-3.5-turbo",
                provider="openai",
                is_free=False,
                cost_per_1k_tokens_input=0.0015,
                cost_per_1k_tokens_output=0.002,
                source_url="https://openai.com/pricing"
            ),
            
            # Anthropic 系列
            ModelPolicy(
                model_name="claude-3-5-sonnet",
                provider="anthropic",
                is_free=False,
                free_quota="新用户注册送额度",
                cost_per_1k_tokens_input=0.003,
                cost_per_1k_tokens_output=0.015,
                source_url="https://www.anthropic.com/pricing"
            ),
            ModelPolicy(
                model_name="claude-3-haiku",
                provider="anthropic",
                is_free=False,
                cost_per_1k_tokens_input=0.00025,
                cost_per_1k_tokens_output=0.00125,
                source_url="https://www.anthropic.com/pricing"
            ),
            
            # Google 系列
            ModelPolicy(
                model_name="gemini-1.5-flash",
                provider="google",
                is_free=False,
                free_quota="免费额度限制",
                cost_per_1k_tokens_input=0.000075,
                cost_per_1k_tokens_output=0.0003,
                source_url="https://ai.google.dev/pricing"
            ),
            ModelPolicy(
                model_name="gemini-1.5-pro",
                provider="google",
                is_free=False,
                cost_per_1k_tokens_input=0.0035,
                cost_per_1k_tokens_output=0.0105,
                source_url="https://ai.google.dev/pricing"
            ),
            
            # Ollama 本地模型（完全免费）
            ModelPolicy(
                model_name="ollama-llama3",
                provider="ollama",
                is_free=True,
                free_quota="完全免费，本地运行",
                notes="本地部署 Llama 3，零成本",
                source_url="https://ollama.com/"
            ),
            ModelPolicy(
                model_name="ollama-qwen2.5",
                provider="ollama",
                is_free=True,
                free_quota="完全免费，本地运行",
                notes="本地部署 Qwen 2.5，零成本，中文优化",
                source_url="https://ollama.com/"
            ),
            ModelPolicy(
                model_name="ollama-mistral",
                provider="ollama",
                is_free=True,
                free_quota="完全免费，本地运行",
                notes="本地部署 Mistral，零成本",
                source_url="https://ollama.com/"
            ),
        ]
        
        for policy in default_policies:
            policy.last_updated = datetime.now().isoformat()
            self.policies[policy.model_name] = policy
    
    def _load_from_cache(self):
        """从缓存加载政策数据"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for model_name, policy_data in data.get('policies', {}).items():
                        policy = ModelPolicy(**policy_data)
                        self.policies[model_name] = policy
                    if 'last_updated' in data:
                        self.last_updated = datetime.fromisoformat(data['last_updated'])
                logger.info(f"✅ 从缓存加载了 {len(self.policies)} 个模型政策")
        except Exception as e:
            logger.warning(f"⚠️ 加载缓存失败: {e}")
    
    def _save_to_cache(self):
        """保存政策数据到缓存"""
        try:
            data = {
                'policies': {name: asdict(policy) for name, policy in self.policies.items()},
                'last_updated': datetime.now().isoformat()
            }
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.last_updated = datetime.now()
        except Exception as e:
            logger.warning(f"⚠️ 保存缓存失败: {e}")
    
    def get_policy(self, model_name: str) -> Optional[ModelPolicy]:
        """获取指定模型的政策"""
        return self.policies.get(model_name)
    
    def get_all_policies(self) -> List[ModelPolicy]:
        """获取所有模型政策"""
        return list(self.policies.values())
    
    def get_free_models(self) -> List[ModelPolicy]:
        """获取所有免费模型"""
        return [p for p in self.policies.values() if p.is_free]
    
    def get_cheapest_models(self, task_type: Optional[str] = None) -> List[ModelPolicy]:
        """获取最便宜的模型（包括免费）"""
        policies = list(self.policies.values())
        
        # 先排免费模型，再按价格排序
        def sort_key(p):
            if p.is_free:
                return (0, 0)
            avg_cost = (p.cost_per_1k_tokens_input + p.cost_per_1k_tokens_output) / 2
            return (1, avg_cost)
        
        policies.sort(key=sort_key)
        return policies
    
    def estimate_cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int
    ) -> CostEstimate:
        """
        预估使用成本
        """
        policy = self.policies.get(model_name)
        if not policy:
            return CostEstimate(
                model_name=model_name,
                estimated_input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
                estimated_cost=0.0,
                is_free=False,
                warning="未知模型，无法预估成本"
            )
        
        if policy.is_free:
            return CostEstimate(
                model_name=model_name,
                estimated_input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
                estimated_cost=0.0,
                is_free=True,
                free_quota_remaining=policy.free_quota
            )
        
        # 计算成本
        input_cost = (input_tokens / 1000) * policy.cost_per_1k_tokens_input
        output_cost = (output_tokens / 1000) * policy.cost_per_1k_tokens_output
        total_cost = input_cost + output_cost
        
        warning = None
        if total_cost > 0.1:  # 超过 $0.1 提醒
            warning = f"⚠️ 预估成本较高: ${total_cost:.4f}"
        
        return CostEstimate(
            model_name=model_name,
            estimated_input_tokens=input_tokens,
            estimated_output_tokens=output_tokens,
            estimated_cost=total_cost,
            is_free=False,
            warning=warning
        )
    
    def should_ask_user(self, model_name: str, input_tokens: int, output_tokens: int) -> bool:
        """
        判断是否需要询问用户（成本超过阈值时）
        """
        estimate = self.estimate_cost(model_name, input_tokens, output_tokens)
        return not estimate.is_free and estimate.estimated_cost > 0.05  # 超过 $0.05 询问
    
    async def fetch_latest_policies(self):
        """
        异步获取最新模型政策
        这里可以集成各平台的 API 来获取实时定价
        """
        logger.info("🔍 检查最新模型政策...")
        
        # TODO: 实际项目中，可以集成以下平台的 API
        # - DeepSeek API
        # - 智谱 AI API
        # - OpenAI API
        # - Anthropic API
        # - 等等
        
        # 暂时只更新时间戳
        for policy in self.policies.values():
            policy.last_updated = datetime.now().isoformat()
        
        self._save_to_cache()
        logger.info("✅ 模型政策已更新")
    
    def update_policy(self, model_name: str, **kwargs):
        """更新模型政策"""
        if model_name in self.policies:
            for key, value in kwargs.items():
                if hasattr(self.policies[model_name], key):
                    setattr(self.policies[model_name], key, value)
            self.policies[model_name].last_updated = datetime.now().isoformat()
            self._save_to_cache()
    
    def get_roi_report(self) -> Dict[str, Any]:
        """
        生成 ROI 报告
        """
        free_models = self.get_free_models()
        cheapest_paid = self.get_cheapest_models()[1:] if self.get_cheapest_models() else []
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_models": len(self.policies),
            "free_models_count": len(free_models),
            "free_models": [
                {
                    "name": m.model_name,
                    "provider": m.provider,
                    "quota": m.free_quota,
                    "notes": m.notes
                }
                for m in free_models
            ],
            "top_5_cheapest_paid": [
                {
                    "name": m.model_name,
                    "provider": m.provider,
                    "avg_cost_per_1k": (m.cost_per_1k_tokens_input + m.cost_per_1k_tokens_output) / 2,
                    "notes": m.notes
                }
                for m in cheapest_paid[:5]
            ],
            "recommendation": "优先使用免费模型（Ollama 本地模型或 GLM-4-Flash），成本敏感时选择 DeepSeek，高质量需求选择 Claude/GPT-4。"
        }


# 全局追踪器实例
policy_tracker = ModelPolicyTracker()
