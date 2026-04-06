import pytest
from src.core.llm import LLMMessage, LLMResponse, ToolCall


def test_llm_message_creation():
    """测试 LLMMessage 创建"""
    message = LLMMessage(role="user", content="Hello, world!")
    assert message.role == "user"
    assert message.content == "Hello, world!"


def test_llm_response_creation():
    """测试 LLMResponse 创建"""
    tool_call = ToolCall(name="get_weather", arguments={"city": "Beijing"})
    response = LLMResponse(
        text="It's sunny in Beijing",
        usage={"prompt_tokens": 10, "completion_tokens": 5},
        tool_calls=[tool_call]
    )
    assert response.text == "It's sunny in Beijing"
    assert response.usage == {"prompt_tokens": 10, "completion_tokens": 5}
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "get_weather"
