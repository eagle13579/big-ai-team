"""MCP (Model Context Protocol) 协议处理模块"""

import json
from typing import Any


class MCPProtocol:
    """MCP协议处理器"""

    def __init__(self):
        self.tools = {}

    def register_tool(self, name: str, handler: callable):
        """注册工具"""
        self.tools[name] = handler

    def process_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """处理MCP请求"""
        try:
            method = request.get("method")
            params = request.get("params", {})

            if method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})

                if tool_name in self.tools:
                    result = self.tools[tool_name](**arguments)
                    return {"jsonrpc": "2.0", "result": result, "id": request.get("id")}
                else:
                    return {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Tool not found: {tool_name}"},
                        "id": request.get("id"),
                    }
            elif method == "tools/list":
                return {
                    "jsonrpc": "2.0",
                    "result": {"tools": list(self.tools.keys())},
                    "id": request.get("id"),
                }
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": request.get("id"),
                }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
                "id": request.get("id"),
            }

    def serialize_response(self, response: dict[str, Any]) -> str:
        """序列化响应"""
        return json.dumps(response)

    def deserialize_request(self, data: str) -> dict[str, Any]:
        """反序列化请求"""
        return json.loads(data)
