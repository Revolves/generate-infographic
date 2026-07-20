"""配置管理模块 - 三模型独立配置

支持独立配置对话模型、多模态模型和生图模型的 URL、API Key 和模型名称。
三种模型可来自不同供应商，也可共用同一套配置。

环境变量退避链:
  CHAT_* → SENSENOVA_* → default
  MULTIMODAL_* → CHAT_* → SENSENOVA_* → default
  IMAGE_* → MULTIMODAL_* → CHAT_* → SENSENOVA_* → default
"""

import logging
import os
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

from infographics_agent.exceptions import ConfigError

logger = logging.getLogger("infographics_agent")


@dataclass(frozen=True)
class ModelEndpoint:
    """单个模型端点配置"""
    api_key: str
    base_url: str
    model: str


@dataclass(frozen=True)
class Config:
    """三模型独立配置

    Attributes:
        chat: 对话/分析模型端点配置
        multimodal: 多模态理解模型端点配置
        image: 信息图生成模型端点配置
        image_size: 默认图片尺寸 (如 "2752x1536")
        num_images: 每次生成图片数量
        request_timeout: HTTP 请求超时秒数
        max_retries: 最大重试次数
        output_dir: 输出目录
    """

    # 三个独立模型端点
    chat: ModelEndpoint
    multimodal: ModelEndpoint
    image: ModelEndpoint

    # 共享配置
    image_size: str = "2752x1536"
    num_images: int = 1
    request_timeout: int = 120
    max_retries: int = 3
    output_dir: str = "output"


def _get_env_with_fallback(
    key: str,
    fallback_keys: list[str],
    default: str = "",
) -> str:
    """从环境变量读取值，支持多级退避

    Args:
        key: 首选环境变量名
        fallback_keys: 退避环境变量名列表（按优先级降序）
        default: 最终默认值

    Returns:
        环境变量值或默认值
    """
    value = os.getenv(key)
    if value:
        return value
    for fb_key in fallback_keys:
        value = os.getenv(fb_key)
        if value:
            return value
    return default


def load_config(env_file: Optional[str] = None) -> Config:
    """从 .env 文件和环境变量加载配置

    Args:
        env_file: .env 文件路径，默认从项目根目录查找

    Returns:
        Config 对象

    Raises:
        ConfigError: 缺少必填配置项
    """
    # 加载 .env 文件
    if env_file:
        load_dotenv(env_file)
    else:
        # 从项目根目录查找
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)

    # ─── 退避链默认值 ───
    _SENSENOVA_DEFAULT = "https://token.sensenova.cn/v1"
    _CHAT_MODEL_DEFAULT = "sensenova-6.7-flash-lite"
    _IMAGE_MODEL_DEFAULT = "sensenova-u1-fast"

    # ─── 读取旧版共享配置（作为退避基准） ───
    legacy_api_key = os.getenv("SENSENOVA_API_KEY", "")
    legacy_base_url = os.getenv("SENSENOVA_BASE_URL", _SENSENOVA_DEFAULT).rstrip("/")

    # ─── 对话模型 ───
    chat_api_key = _get_env_with_fallback(
        "CHAT_API_KEY", [], legacy_api_key
    )
    chat_base_url = _get_env_with_fallback(
        "CHAT_BASE_URL", [], legacy_base_url
    )
    chat_model = _get_env_with_fallback(
        "CHAT_MODEL", [], _CHAT_MODEL_DEFAULT
    )

    # ─── 多模态模型 ───
    multimodal_api_key = _get_env_with_fallback(
        "MULTIMODAL_API_KEY", ["CHAT_API_KEY"], chat_api_key
    )
    multimodal_base_url = _get_env_with_fallback(
        "MULTIMODAL_BASE_URL", ["CHAT_BASE_URL"], chat_base_url
    )
    multimodal_model = _get_env_with_fallback(
        "MULTIMODAL_MODEL", ["CHAT_MODEL"], chat_model
    )

    # ─── 生图模型 ───
    image_api_key = _get_env_with_fallback(
        "IMAGE_API_KEY", ["MULTIMODAL_API_KEY", "CHAT_API_KEY"], multimodal_api_key
    )
    image_base_url = _get_env_with_fallback(
        "IMAGE_BASE_URL", ["MULTIMODAL_BASE_URL", "CHAT_BASE_URL"], multimodal_base_url
    )
    image_model = _get_env_with_fallback(
        "IMAGE_MODEL", [], _IMAGE_MODEL_DEFAULT
    )

    # ─── 共享配置 ───
    image_size = os.getenv("IMAGE_SIZE", "2752x1536")
    request_timeout = int(os.getenv("REQUEST_TIMEOUT", "120"))
    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    output_dir = os.getenv("OUTPUT_DIR", "output")

    # ─── 验证 ───
    if not any([chat_api_key, multimodal_api_key, image_api_key]):
        raise ConfigError(
            "未配置 API Key。\n"
            "请设置环境变量或在 .env 文件中配置:\n"
            "  SENSENOVA_API_KEY=your_api_key_here\n"
            "或单独配置各模型:\n"
            "  CHAT_API_KEY=...\n"
            "  MULTIMODAL_API_KEY=...\n"
            "  IMAGE_API_KEY=..."
        )

    # 如果某个模型的 base_url 与退避目标不同，但该模型未设置独立 key → 警告
    if chat_base_url != legacy_base_url and not os.getenv("CHAT_API_KEY"):
        warnings.warn(
            "CHAT_BASE_URL 与 SENSENOVA_BASE_URL 不同，但未设置 CHAT_API_KEY。"
            "将使用 SENSENOVA_API_KEY 进行认证。"
        )
    if multimodal_base_url != chat_base_url and not os.getenv("MULTIMODAL_API_KEY"):
        warnings.warn(
            "MULTIMODAL_BASE_URL 与 CHAT_BASE_URL 不同，但未设置 MULTIMODAL_API_KEY。"
            "将使用 CHAT_API_KEY 进行认证。"
        )
    if image_base_url != multimodal_base_url and not os.getenv("IMAGE_API_KEY"):
        warnings.warn(
            "IMAGE_BASE_URL 与 MULTIMODAL_BASE_URL 不同，但未设置 IMAGE_API_KEY。"
            "将使用 MULTIMODAL_API_KEY 进行认证。"
        )

    return Config(
        chat=ModelEndpoint(
            api_key=chat_api_key,
            base_url=chat_base_url,
            model=chat_model,
        ),
        multimodal=ModelEndpoint(
            api_key=multimodal_api_key,
            base_url=multimodal_base_url,
            model=multimodal_model,
        ),
        image=ModelEndpoint(
            api_key=image_api_key,
            base_url=image_base_url,
            model=image_model,
        ),
        image_size=image_size,
        num_images=1,
        request_timeout=request_timeout,
        max_retries=max_retries,
        output_dir=output_dir,
    )


def ensure_output_dir(config: Config) -> Path:
    """确保输出目录存在

    Args:
        config: 配置对象

    Returns:
        输出目录的绝对路径
    """
    output_path = Path(config.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path.resolve()