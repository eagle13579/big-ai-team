class ToolError(Exception):
    """
    工具异常基类
    """
    pass


class ToolNotFoundError(ToolError):
    """
    工具未找到异常
    """
    def __init__(self, tool_name: str):
        super().__init__(f"Tool '{tool_name}' not found")
        self.tool_name = tool_name


class ToolExecutionError(ToolError):
    """
    工具执行异常
    """
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Error executing tool '{tool_name}': {message}")
        self.tool_name = tool_name
        self.message = message


class ToolValidationError(ToolError):
    """
    工具参数验证异常
    """
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Validation error for tool '{tool_name}': {message}")
        self.tool_name = tool_name
        self.message = message


class ToolTimeoutError(ToolError):
    """
    工具执行超时异常
    """
    def __init__(self, tool_name: str, timeout: int):
        super().__init__(f"Tool '{tool_name}' execution timed out after {timeout} seconds")
        self.tool_name = tool_name
        self.timeout = timeout


class LLMError(ToolError):
    """
    LLM 调用异常
    """
    def __init__(self, message: str):
        super().__init__(f"LLM error: {message}")
        self.message = message