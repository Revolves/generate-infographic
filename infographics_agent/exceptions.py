"""Infographics Agent 自定义异常"""


class InfographicsError(Exception):
    """基础异常"""
    pass


class AuthError(InfographicsError):
    """认证错误 (401/403)"""
    pass


class RateLimitError(InfographicsError):
    """频率限制 (429)"""
    pass


class ModelNotFoundError(InfographicsError):
    """模型不存在 (404)"""
    pass


class InvalidRequestError(InfographicsError):
    """无效请求 (400)"""
    pass


class ServerError(InfographicsError):
    """服务器错误 (500)"""
    pass


class ConfigError(InfographicsError):
    """配置错误"""
    pass