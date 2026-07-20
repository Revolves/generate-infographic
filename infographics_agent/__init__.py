"""Infographics Agent - 基于 AI 的信息图生成工具

通过多模态 AI 模型分析用户需求，自动生成专业信息图。
支持独立配置对话模型、多模态模型和生图模型。
"""

__version__ = "0.2.0"

from infographics_agent.config import Config, load_config
from infographics_agent.client import InfographicsClient
from infographics_agent.agent import InfographicAgent
from infographics_agent.exceptions import (
    InfographicsError,
    AuthError,
    ConfigError,
    RateLimitError,
    ModelNotFoundError,
    InvalidRequestError,
    ServerError,
)

__all__ = [
    "Config",
    "load_config",
    "InfographicsClient",
    "InfographicAgent",
    "InfographicsError",
    "AuthError",
    "ConfigError",
    "RateLimitError",
    "ModelNotFoundError",
    "InvalidRequestError",
    "ServerError",
]