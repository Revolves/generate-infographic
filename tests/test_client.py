"""测试 client 模块 — API 客户端"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from infographics_agent.client import InfographicsClient
from infographics_agent.config import Config, ModelEndpoint
from infographics_agent.exceptions import AuthError, InvalidRequestError, RateLimitError, ServerError


@pytest.fixture
def mock_config():
    """创建测试用配置"""
    return Config(
        chat=ModelEndpoint(api_key="sk-chat", base_url="https://chat.example.com/v1", model="gpt-4o"),
        multimodal=ModelEndpoint(api_key="sk-mm", base_url="https://mm.example.com/v1", model="claude-3-sonnet"),
        image=ModelEndpoint(api_key="sk-img", base_url="https://img.example.com/v1", model="dall-e-3"),
        image_size="2752x1536",
        request_timeout=30,
        max_retries=1,
        output_dir="/tmp/test_output",
    )


class TestInfographicsClient:
    """测试 InfographicsClient"""

    def test_init_creates_no_sessions(self, mock_config):
        """初始化时不创建 Session（懒加载）"""
        client = InfographicsClient(mock_config)
        assert client._chat_session is None
        assert client._multimodal_session is None
        assert client._image_session is None
        client.close()

    def test_get_chat_session(self, mock_config):
        """获取对话 Session"""
        client = InfographicsClient(mock_config)
        session = client._get_chat_session()
        assert session is not None
        assert session.headers["Authorization"] == "Bearer sk-chat"
        assert client._chat_session is not None
        client.close()

    def test_get_multimodal_session(self, mock_config):
        """获取多模态 Session"""
        client = InfographicsClient(mock_config)
        session = client._get_multimodal_session()
        assert session is not None
        assert session.headers["Authorization"] == "Bearer sk-mm"
        client.close()

    def test_get_image_session(self, mock_config):
        """获取生图 Session"""
        client = InfographicsClient(mock_config)
        session = client._get_image_session()
        assert session is not None
        assert session.headers["Authorization"] == "Bearer sk-img"
        client.close()

    @patch("requests.Session.post")
    def test_multimodal_analyze(self, mock_post, mock_config):
        """测试多模态分析"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "分析结果"}}]
        }
        mock_post.return_value = mock_response

        client = InfographicsClient(mock_config)
        result = client.multimodal_analyze("分析这张图片", system_prompt="你是一个专家")
        assert result == "分析结果"
        client.close()

        # 验证调用参数
        call_args = mock_post.call_args
        assert call_args is not None
        url = call_args[0][0]
        payload = call_args[1]["json"]
        assert "mm.example.com" in url
        assert payload["model"] == "claude-3-sonnet"

    @patch("requests.Session.post")
    def test_generate_infographic(self, mock_post, mock_config):
        """测试生成信息图"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{"url": "https://example.com/img.png"}]
        }
        mock_post.return_value = mock_response

        client = InfographicsClient(mock_config)
        result = client.generate_infographic("一张科技感信息图", size="2752x1536")
        assert len(result) == 1
        assert result[0]["url"] == "https://example.com/img.png"
        client.close()

        # 验证调用参数
        call_args = mock_post.call_args
        assert call_args is not None
        url = call_args[0][0]
        payload = call_args[1]["json"]
        assert "img.example.com" in url
        assert payload["model"] == "dall-e-3"

    @patch("requests.Session.post")
    def test_chat_analyze(self, mock_post, mock_config):
        """测试纯文本对话"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "你好！"}}]
        }
        mock_post.return_value = mock_response

        client = InfographicsClient(mock_config)
        result = client.chat_analyze("你好", system_prompt="你是一个助手")
        assert result == "你好！"
        client.close()

        call_args = mock_post.call_args
        assert call_args is not None
        url = call_args[0][0]
        assert "chat.example.com" in url

    @pytest.mark.parametrize("status,expected_exception", [
        (400, InvalidRequestError),
        (401, AuthError),
        (403, AuthError),
        (429, RateLimitError),
        (500, ServerError),
    ])
    @patch("requests.Session.post")
    def test_error_handling(self, mock_post, mock_config, status, expected_exception):
        """测试错误处理"""
        mock_response = Mock()
        mock_response.status_code = status
        mock_response.json.return_value = {"error": {"message": "test error"}}
        mock_response.text = '{"error": {"message": "test error"}}'
        mock_post.return_value = mock_response

        client = InfographicsClient(mock_config)
        with pytest.raises(expected_exception):
            client.chat_analyze("test")
        client.close()

    @patch("requests.Session.post")
    def test_retry_on_timeout(self, mock_post, mock_config):
        """测试超时重试"""
        mock_post.side_effect = [
            requests.Timeout("timeout"),
            Mock(status_code=200, json=lambda: {"choices": [{"message": {"content": "ok"}}]}),
        ]

        client = InfographicsClient(mock_config)
        result = client.chat_analyze("test")
        assert result == "ok"
        assert mock_post.call_count == 2
        client.close()

    @patch("requests.Session.post")
    def test_retry_exhausted(self, mock_post, mock_config):
        """测试重试耗尽"""
        mock_post.side_effect = requests.Timeout("timeout")

        client = InfographicsClient(mock_config)
        with pytest.raises(ServerError, match="网络错误"):
            client.chat_analyze("test")
        assert mock_post.call_count == mock_config.max_retries + 1
        client.close()

    def test_enter_exit(self, mock_config):
        """测试上下文管理器"""
        with InfographicsClient(mock_config) as client:
            assert client._chat_session is None  # 懒加载，未使用
        # 退出后不会报错
        client.close()

    def test_multimodal_fallback_to_chat(self, mock_config):
        """多模态模型在 multimodal API key 为空时退避到 chat"""
        config = Config(
            chat=ModelEndpoint(api_key="sk-chat", base_url="https://chat.example.com/v1", model="gpt-4o"),
            multimodal=ModelEndpoint(api_key="", base_url="https://chat.example.com/v1", model="gpt-4o"),
            image=ModelEndpoint(api_key="sk-img", base_url="https://img.example.com/v1", model="dall-e-3"),
        )
        client = InfographicsClient(config)
        mm_session = client._get_multimodal_session()
        assert mm_session.headers["Authorization"] == "Bearer sk-chat"
        client.close()