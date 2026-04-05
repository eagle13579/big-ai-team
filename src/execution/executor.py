from typing import Dict, Any, Optional
from .mcp.protocol import MCPProtocol


class ToolExecutor:
    """工具执行器"""
    
    def __init__(self):
        self.mcp_protocol = MCPProtocol()
        self._register_default_tools()
    
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        try:
            # 构建MCP请求
            request = {
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments
                }
            }
            
            # 处理请求
            response = self.mcp_protocol.process_request(request)
            
            if "error" in response:
                return {
                    "success": False,
                    "error": response["error"]["message"]
                }
            else:
                return {
                    "success": True,
                    "result": response["result"]
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _register_default_tools(self):
        """注册默认工具"""
        self.mcp_protocol.register_tool("read_file", self._read_file)
        self.mcp_protocol.register_tool("write_file", self._write_file)
        self.mcp_protocol.register_tool("list_directory", self._list_directory)
    
    def register_tool(self, name: str, handler: callable):
        """注册工具"""
        self.mcp_protocol.register_tool(name, handler)
    
    def list_tools(self) -> list[str]:
        """列出所有可用工具"""
        request = {"method": "tools/list"}
        response = self.mcp_protocol.process_request(request)
        return response.get("result", {}).get("tools", [])
    
    # 默认工具实现
    def _read_file(self, path: str) -> Dict[str, Any]:
        """读取文件"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return {"content": content}
        except Exception as e:
            return {"error": str(e)}
    
    def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """写入文件"""
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}
    
    def _list_directory(self, path: str) -> Dict[str, Any]:
        """列出目录内容"""
        try:
            import os
            files = os.listdir(path)
            return {"files": files}
        except Exception as e:
            return {"error": str(e)}
