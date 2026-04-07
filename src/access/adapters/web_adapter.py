from typing import Dict, Any, Optional
from ..engine import IntentEngine
from ..router import Dispatcher
from src.shared.logging import logger


class WebAdapter:
    """Web 平台适配器"""
    
    def __init__(self, intent_engine: IntentEngine, dispatcher: Dispatcher):
        self.intent_engine = intent_engine
        self.dispatcher = dispatcher
    
    def process_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理 Web 请求"""
        try:
            # 提取请求参数
            user_input = request_data.get("input", "")
            user_id = request_data.get("user_id", "")
            session_id = request_data.get("session_id", "")
            platform = request_data.get("platform", "web")
            
            # 处理意图
            intent_result = self.intent_engine.process_intent({
                "raw_input": user_input,
                "platform": platform,
                "user_id": user_id,
                "context": request_data.get("context", {})
            })
            
            # 调度任务
            task_result = self.dispatcher.dispatch_task({
                "plan_id": session_id,
                "description": user_input,
                "assignee": "agent",
                "input_params": {
                    "intent": intent_result,
                    "user_input": user_input,
                    "context": request_data.get("context", {})
                }
            })
            
            return {
                "status": "success",
                "data": {
                    "intent": intent_result,
                    "task_id": task_result.task_id,
                    "message": "请求已处理"
                }
            }
        except Exception as e:
            logger.error(f"Web 适配器处理请求失败: {str(e)}")
            return {
                "status": "error",
                "message": f"处理请求失败: {str(e)}"
            }
    
    def format_response(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化响应"""
        return {
            "status": response_data.get("status", "success"),
            "data": response_data.get("data", {}),
            "message": response_data.get("message", ""),
            "timestamp": self._get_timestamp()
        }
    
    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"
