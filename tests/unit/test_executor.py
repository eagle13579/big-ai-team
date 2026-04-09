import pytest
import asyncio
from src.execution.executor import ToolExecutor


class TestToolExecutor:
    """测试工具执行器"""
    
    @pytest.fixture
    def executor(self):
        """创建执行器实例"""
        return ToolExecutor()
    
    @pytest.mark.asyncio
    async def test_execute_valid_tool(self, executor):
        """测试执行有效工具"""
        result = await executor.execute("get_system_status", {})
        assert result["success"] is True
        assert "status" in result["result"]
        assert result["result"]["status"] == "ready"
    
    @pytest.mark.asyncio
    async def test_execute_invalid_tool(self, executor):
        """测试执行无效工具"""
        result = await executor.execute("invalid_tool", {})
        assert result["success"] is False
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_execute_with_timeout(self, executor):
        """测试执行超时"""
        # 创建一个会超时的工具
        async def slow_tool():
            await asyncio.sleep(2)
            return "done"
        
        # 注册工具
        executor.register_tool("slow_tool", slow_tool)
        
        # 执行工具，设置超时时间为 1 秒
        result = await executor.execute("slow_tool", {}, timeout=1)
        assert result["success"] is False
        assert "超时" in result["error"]
    
    @pytest.mark.asyncio
    async def test_execute_with_permission_denied(self, executor):
        """测试权限被拒绝"""
        # 尝试以 guest 角色执行需要 admin 权限的工具
        result = await executor.execute("delete_file", {"filename": "test.txt"}, role="guest")
        assert result["success"] is False
        assert "权限不足" in result["error"]
    
    @pytest.mark.asyncio
    async def test_file_operations(self, executor):
        """测试文件操作工具"""
        # 测试写入文件
        write_result = await executor.execute("write_file", {"filename": "test.txt", "content": "Hello, World!"})
        assert write_result["success"] is True
        
        # 测试读取文件
        read_result = await executor.execute("read_file", {"filename": "test.txt"})
        assert read_result["success"] is True
        assert read_result["result"] == "Hello, World!"
        
        # 测试列出文件
        list_result = await executor.execute("list_files", {})
        assert list_result["success"] is True
        assert "test.txt" in list_result["result"]
        
        # 测试删除文件（需要admin权限）
        delete_result = await executor.execute("delete_file", {"filename": "test.txt"}, role="admin")
        assert delete_result["success"] is True
    
    def test_get_available_tools(self, executor):
        """测试获取可用工具列表"""
        tools = executor.get_available_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert "web_search" in tools
        assert "write_file" in tools
        assert "read_file" in tools
    
    def test_register_and_unregister_tool(self, executor):
        """测试注册和注销工具"""
        # 定义测试工具
        async def test_tool():
            return "test result"
        
        # 注册工具
        executor.register_tool("test_tool", test_tool)
        tools = executor.get_available_tools()
        assert "test_tool" in tools
        
        # 注销工具
        executor.unregister_tool("test_tool")
        tools = executor.get_available_tools()
        assert "test_tool" not in tools
