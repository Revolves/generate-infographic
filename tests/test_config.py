"""测试 config 模块 — 三模型独立配置与退避链"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from infographics_agent.config import Config, ModelEndpoint, load_config
from infographics_agent.exceptions import ConfigError


class TestModelEndpoint:
    """测试 ModelEndpoint 数据类"""

    def test_create_endpoint(self):
        ep = ModelEndpoint(api_key="sk-xxx", base_url="https://api.example.com/v1", model="gpt-4o")
        assert ep.api_key == "sk-xxx"
        assert ep.base_url == "https://api.example.com/v1"
        assert ep.model == "gpt-4o"


class TestLoadConfig:
    """测试 load_config 函数"""

    def test_minimal_config(self):
        """只设置 SENSENOVA_API_KEY 应能正常工作"""
        with patch.dict(os.environ, {"SENSENOVA_API_KEY": "sk-test-key"}, clear=True):
            config = load_config()
            assert config.chat.api_key == "sk-test-key"
            assert config.multimodal.api_key == "sk-test-key"
            assert config.image.api_key == "sk-test-key"
            assert config.chat.model == "sensenova-6.7-flash-lite"
            assert config.image.model == "sensenova-u1-fast"

    def test_three_independent_keys(self):
        """三个模型独立配置"""
        env = {
            "CHAT_API_KEY": "sk-chat",
            "CHAT_BASE_URL": "https://chat.example.com/v1",
            "CHAT_MODEL": "gpt-4o",
            "MULTIMODAL_API_KEY": "sk-mm",
            "MULTIMODAL_BASE_URL": "https://mm.example.com/v1",
            "MULTIMODAL_MODEL": "claude-3-sonnet",
            "IMAGE_API_KEY": "sk-img",
            "IMAGE_BASE_URL": "https://img.example.com/v1",
            "IMAGE_MODEL": "dall-e-3",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.chat.api_key == "sk-chat"
            assert config.chat.model == "gpt-4o"
            assert config.multimodal.api_key == "sk-mm"
            assert config.multimodal.model == "claude-3-sonnet"
            assert config.image.api_key == "sk-img"
            assert config.image.model == "dall-e-3"

    def test_fallback_chain(self):
        """多模态退避到对话，生图退避到多模态"""
        env = {
            "CHAT_API_KEY": "sk-chat",
            "CHAT_BASE_URL": "https://chat.example.com/v1",
            "CHAT_MODEL": "gpt-4o",
            # 没有 MULTIMODAL_API_KEY → 应退避到 CHAT_API_KEY
            "IMAGE_API_KEY": "sk-img",
            "IMAGE_BASE_URL": "https://img.example.com/v1",
            "IMAGE_MODEL": "dall-e-3",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.chat.api_key == "sk-chat"
            assert config.multimodal.api_key == "sk-chat"  # 退避
            assert config.image.api_key == "sk-img"  # 独立

    def test_missing_api_key_raises_error(self):
        """没有 API Key 应抛出 ConfigError"""
        with patch.dict(os.environ, {}, clear=True):
            with patch("infographics_agent.config.load_dotenv", return_value=None):
                with pytest.raises(ConfigError, match="API Key"):
                    load_config()

    def test_shared_config(self):
        """共享配置项"""
        env = {
            "SENSENOVA_API_KEY": "sk-test",
            "IMAGE_SIZE": "2048x2048",
            "REQUEST_TIMEOUT": "60",
            "MAX_RETRIES": "5",
            "OUTPUT_DIR": "/tmp/test_output",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.image_size == "2048x2048"
            assert config.request_timeout == 60
            assert config.max_retries == 5
            assert config.output_dir == "/tmp/test_output"

    def test_legacy_backward_compat(self):
        """旧版 SENSENOVA_* 配置兼容"""
        env = {
            "SENSENOVA_API_KEY": "sk-legacy",
            "SENSENOVA_BASE_URL": "https://legacy.example.com/v1",
            "MULTIMODAL_MODEL": "sensenova-6.7-flash-lite",
            "INFOGRAPHIC_MODEL": "sensenova-u1-fast",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.chat.api_key == "sk-legacy"
            assert config.chat.base_url == "https://legacy.example.com/v1"
            assert config.multimodal.api_key == "sk-legacy"
            assert config.image.model == "sensenova-u1-fast"

    def test_env_file_loading(self):
        """从 .env 文件加载"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False, encoding="utf-8") as f:
            f.write('SENSENOVA_API_KEY=sk-from-file\n')
            f.write('CHAT_MODEL=gpt-4o\n')
            env_path = f.name

        try:
            with patch.dict(os.environ, {}, clear=True):
                config = load_config(env_path)
                assert config.chat.api_key == "sk-from-file"
                assert config.chat.model == "gpt-4o"
        finally:
            Path(env_path).unlink(missing_ok=True)