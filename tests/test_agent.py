"""测试 agent 模块 — 主编排器"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from infographics_agent.agent import InfographicAgent
from infographics_agent.config import Config, ModelEndpoint


@pytest.fixture
def mock_config():
    """创建测试用配置"""
    return Config(
        chat=ModelEndpoint(api_key="sk-test", base_url="https://test.example.com/v1", model="test-chat"),
        multimodal=ModelEndpoint(api_key="sk-test", base_url="https://test.example.com/v1", model="test-mm"),
        image=ModelEndpoint(api_key="sk-test", base_url="https://test.example.com/v1", model="test-img"),
        image_size="2752x1536",
        request_timeout=30,
        max_retries=1,
        output_dir=tempfile.mkdtemp(),
    )


@pytest.fixture
def sample_requirements():
    """创建示例需求文件"""
    data = {
        "purpose": "测试信息图",
        "audience": "开发者",
        "key_data": "Python 3.10 发布\n新增模式匹配语法",
        "narrative": "自上而下",
        "style": "简约风格",
        "layout": "竖版",
        "brand": "无",
        "image_paths": [],
        "additional_notes": "",
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False, encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
        return f.name


class TestInfographicAgent:
    """测试 InfographicAgent"""

    def test_init(self, mock_config):
        agent = InfographicAgent(mock_config)
        assert agent.config is not None
        assert agent.client is not None
        assert agent.output_dir is not None
        assert agent.max_improve_rounds == 10
        agent.close()

    def test_load_requirements_valid(self, mock_config, sample_requirements):
        agent = InfographicAgent(mock_config)
        req = agent._load_requirements(sample_requirements)
        assert req["purpose"] == "测试信息图"
        assert req["audience"] == "开发者"
        agent.close()

    def test_load_requirements_not_found(self, mock_config):
        agent = InfographicAgent(mock_config)
        with pytest.raises(FileNotFoundError):
            agent._load_requirements("/nonexistent/requirements.json")
        agent.close()

    def test_parse_analysis_response_json(self, mock_config):
        """测试解析 JSON 格式的分析响应"""
        agent = InfographicAgent(mock_config)
        response = json.dumps({
            "主题与目的": "测试主题",
            "视觉风格": "简约风格",
            "布局建议": "自上而下",
        }, ensure_ascii=False)
        result = agent._parse_analysis_response(response, {})
        assert result["theme"] == "测试主题"
        assert result["style_description"] == "简约风格"
        agent.close()

    def test_parse_analysis_response_fallback(self, mock_config):
        """测试非 JSON 响应时的回退"""
        agent = InfographicAgent(mock_config)
        result = agent._parse_analysis_response("非结构化文本", {"purpose": "回退主题"})
        assert result["theme"] == "回退主题"
        agent.close()

    def test_parse_updated_requirements(self, mock_config):
        """测试解析更新后的需求"""
        agent = InfographicAgent(mock_config)
        response = '{"purpose": "新主题", "style": "新风格"}'
        original = {"purpose": "旧主题", "audience": "开发者", "key_data": "数据"}
        result = agent._parse_updated_requirements(response, original)
        assert result["purpose"] == "新主题"
        assert result["audience"] == "开发者"  # 保留未修改字段
        agent.close()

    def test_parse_updated_requirements_fallback(self, mock_config):
        """测试解析失败的退避"""
        agent = InfographicAgent(mock_config)
        result = agent._parse_updated_requirements("无效内容", {"purpose": "原始"})
        assert result["purpose"] == "原始"
        agent.close()

    @pytest.mark.parametrize("size_str,expected", [
        ("2752x1536", "2752x1536"),
        ("1920×1080", "2752x1536"),  # 1920x1080 不在有效尺寸中，按比例匹配
        ("", "2752x1536"),  # 空字符串，返回默认
    ])
    def test_resolve_size(self, mock_config, size_str, expected):
        """测试尺寸解析"""
        agent = InfographicAgent(mock_config)
        result = agent._resolve_size(size_str)
        assert result is not None
        assert "x" in result

    def test_flatten_to_text(self, mock_config):
        """测试展平嵌套字典"""
        agent = InfographicAgent(mock_config)
        result = agent._flatten_to_text({"key1": "value1", "key2": ["a", "b"]})
        assert "key1" in result
        assert "value1" in result
        assert "a" in result

    def test_enter_exit(self, mock_config):
        """测试上下文管理器"""
        with InfographicAgent(mock_config) as agent:
            assert agent.config is not None
        # 退出后不会报错

    def test_analyze_only(self, mock_config, sample_requirements):
        """测试预览模式正常流程"""
        agent = InfographicAgent(mock_config)
        with patch.object(agent.client, 'multimodal_analyze', return_value='{"theme": "测试主题"}'):
            result = agent.analyze_only(sample_requirements)
            assert result["status"] == "preview"
            assert "analysis" in result
            assert "prompt" in result
        agent.close()

    @pytest.mark.parametrize("key,expected", [
        ("image_paths", []),
        ("brand", "无"),
    ])
    def test_requirements_common_fields(self, mock_config, sample_requirements, key, expected):
        """测试需求字段常见值"""
        agent = InfographicAgent(mock_config)
        req = agent._load_requirements(sample_requirements)
        assert req.get(key, None) == expected
        agent.close()

    def test_cleanup(self, sample_requirements):
        """测试清理"""
        # 创建临时配置
        temp_dir = tempfile.mkdtemp()
        config = Config(
            chat=ModelEndpoint(api_key="sk-test", base_url="https://test.example.com/v1", model="test-chat"),
            multimodal=ModelEndpoint(api_key="sk-test", base_url="https://test.example.com/v1", model="test-mm"),
            image=ModelEndpoint(api_key="sk-test", base_url="https://test.example.com/v1", model="test-img"),
            output_dir=temp_dir,
        )
        agent = InfographicAgent(config)
        agent.close()  # 不应报错