from typing import Any

from ..shared.schemas import IntentRequest


class IntentEngine:
    """意图识别引擎"""

    def __init__(self):
        self.keywords = {
            "设计": ["design", "architecture", "schema"],
            "开发": ["develop", "code", "implement"],
            "分析": ["analyze", "analyze", "evaluate"],
            "测试": ["test", "verify", "validate"],
            "部署": ["deploy", "release", "publish"],
        }

    def process_intent(self, intent: IntentRequest) -> dict[str, Any]:
        """处理意图"""
        raw_input = intent.raw_input
        intent_type = self._detect_intent_type(raw_input)
        confidence = self._calculate_confidence(raw_input, intent_type)

        return {
            "intent_type": intent_type,
            "confidence": confidence,
            "raw_input": raw_input,
            "platform": intent.platform,
            "user_id": intent.user_id,
            "context": intent.context,
        }

    def _detect_intent_type(self, text: str) -> str:
        """检测意图类型"""
        for intent_type, keywords in self.keywords.items():
            if any(keyword in text for keyword in keywords):
                return intent_type
        return "general"

    def _calculate_confidence(self, text: str, intent_type: str) -> float:
        """计算置信度"""
        if intent_type == "general":
            return 0.5

        keywords = self.keywords.get(intent_type, [])
        matched_count = sum(1 for keyword in keywords if keyword in text)
        total_keywords = len(keywords)

        if total_keywords == 0:
            return 0.5

        return min(1.0, matched_count / total_keywords)

    def extract_entities(self, text: str) -> dict[str, Any]:
        """提取实体"""
        # 简单的实体提取示例
        entities = {}

        # 提取API相关实体
        if "API" in text or "api" in text:
            entities["resource_type"] = "API"

        # 提取代码相关实体
        if "code" in text or "代码" in text:
            entities["resource_type"] = "code"

        return entities
