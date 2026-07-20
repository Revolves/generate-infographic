"""API 客户端 - 多模型端点支持

支持三个独立模型端点，每个端点可配置不同的 API Key、Base URL 和模型名称。
使用 OpenAI 兼容接口进行通信。
"""

import base64
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from infographics_agent.config import Config
from infographics_agent.exceptions import (
    AuthError,
    InvalidRequestError,
    ModelNotFoundError,
    RateLimitError,
    ServerError,
)

logger = logging.getLogger("infographics_agent")


class InfographicsClient:
    """信息图 API 客户端 (OpenAI 兼容接口)

    管理三个独立的模型端点：
    - chat: 对话/分析模型
    - multimodal: 多模态理解模型（退避到 chat）
    - image: 信息图生成模型

    每个端点拥有独立的 Session 和认证信息。
    """

    def __init__(self, config: Config):
        self.config = config

        # 三个独立 Session（懒加载，按需创建）
        self._chat_session: Optional[requests.Session] = None
        self._multimodal_session: Optional[requests.Session] = None
        self._image_session: Optional[requests.Session] = None

    # ─── Session 管理 ─────────────────────────────────────────

    def _get_chat_session(self) -> requests.Session:
        if self._chat_session is None:
            self._chat_session = self._create_session(self.config.chat.api_key)
        return self._chat_session

    def _get_multimodal_session(self) -> requests.Session:
        if self._multimodal_session is None:
            key = self.config.multimodal.api_key or self.config.chat.api_key
            self._multimodal_session = self._create_session(key)
        return self._multimodal_session

    def _get_image_session(self) -> requests.Session:
        if self._image_session is None:
            key = self.config.image.api_key or self.config.multimodal.api_key or self.config.chat.api_key
            self._image_session = self._create_session(key)
        return self._image_session

    @staticmethod
    def _create_session(api_key: str) -> requests.Session:
        session = requests.Session()
        session.headers.update({
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "InfographicsAgent/0.2.0",
        })
        return session

    # ─── 多模态分析 ───────────────────────────────────────────

    def multimodal_analyze(
        self,
        text: str,
        image_paths: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> str:
        """使用多模态模型分析图文需求 (OpenAI 兼容)

        Args:
            text: 用户输入的文本需求
            image_paths: 参考图片路径列表
            system_prompt: 系统提示词
            max_tokens: 最大输出 token 数
            temperature: 采样温度

        Returns:
            分析结果文本
        """
        content: List[Dict[str, Any]] = [{"type": "text", "text": text}]

        if image_paths:
            for img_path in image_paths:
                mime, b64_data = self._encode_image(img_path)
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime};base64,{b64_data}"},
                })

        messages = [{"role": "user", "content": content}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        payload = {
            "model": self.config.multimodal.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "reasoning_effort": "none",
        }

        result = self._call_api(
            "chat/completions",
            payload,
            session=self._get_multimodal_session(),
            base_url=self.config.multimodal.base_url,
        )
        return result["choices"][0]["message"]["content"]

    # ─── 纯文本对话 ───────────────────────────────────────────

    def chat_analyze(
        self,
        text: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        reasoning_effort: Optional[str] = None,
    ) -> str:
        """使用对话模型进行纯文本分析 (OpenAI 兼容)

        Args:
            text: 输入文本
            system_prompt: 系统提示词
            max_tokens: 最大输出 token 数
            temperature: 采样温度
            reasoning_effort: 推理力度 (low/medium/high/none)

        Returns:
            模型响应文本
        """
        messages = [{"role": "user", "content": text}]
        if system_prompt:
            messages.insert(0, {"role": "system", "content": system_prompt})

        payload: Dict[str, Any] = {
            "model": self.config.chat.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if reasoning_effort:
            payload["reasoning_effort"] = reasoning_effort

        result = self._call_api(
            "chat/completions",
            payload,
            session=self._get_chat_session(),
            base_url=self.config.chat.base_url,
        )
        return result["choices"][0]["message"]["content"]

    # ─── 信息图生成 ───────────────────────────────────────────

    def generate_infographic(
        self,
        prompt: str,
        size: Optional[str] = None,
        num_images: Optional[int] = None,
        **extra_params: Any,
    ) -> List[Dict[str, Any]]:
        """生成信息图 (OpenAI 兼容 images/generations)

        Args:
            prompt: 信息图描述提示词
            size: 图片尺寸 (如 "2752x1536")
            num_images: 生成数量
            **extra_params: 额外模型参数（自优化循环中动态调整）

        Returns:
            生成结果列表 [{"url": "..."}]
        """
        payload: Dict[str, Any] = {
            "model": self.config.image.model,
            "prompt": prompt,
            "n": num_images or self.config.num_images,
            "size": size or self.config.image_size,
        }
        payload.update(extra_params)

        result = self._call_api(
            "images/generations",
            payload,
            session=self._get_image_session(),
            base_url=self.config.image.base_url,
        )
        return result.get("data", [])

    # ─── 图片下载 ─────────────────────────────────────────────

    def download_image(self, url: str, output_dir: Optional[str] = None) -> Path:
        """下载生成的图片到本地

        Args:
            url: 图片 URL (有效期 1 小时)
            output_dir: 输出目录

        Returns:
            本地文件路径
        """
        out_dir = Path(output_dir or self.config.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"infographic_{timestamp}.png"
        filepath = out_dir / filename

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        resp = requests.get(
            url,
            headers=headers,
            timeout=self.config.request_timeout,
        )
        resp.raise_for_status()

        with open(filepath, "wb") as f:
            f.write(resp.content)

        logger.info(f"图片已下载: {filepath}")
        return filepath.resolve()

    # ─── 内部方法 ─────────────────────────────────────────────

    def _call_api(
        self,
        endpoint: str,
        payload: Dict[str, Any],
        session: requests.Session,
        base_url: str,
    ) -> Dict[str, Any]:
        """调用 API (带重试)

        Args:
            endpoint: 如 "chat/completions" 或 "images/generations"
            payload: 请求体 JSON
            session: 使用的 requests Session
            base_url: API 基础 URL

        Returns:
            API 响应 JSON
        """
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        last_error: Optional[Exception] = None

        for attempt in range(self.config.max_retries + 1):
            try:
                resp = session.post(
                    url, json=payload, timeout=self.config.request_timeout,
                )
                if resp.status_code == 200:
                    return resp.json()

                self._handle_error(resp, endpoint)

            except (requests.ConnectionError, requests.Timeout) as e:
                last_error = e
                if attempt < self.config.max_retries:
                    wait = min(2 ** attempt * 1.5, 30)
                    logger.warning(f"网络错误 (尝试 {attempt+1}/{self.config.max_retries+1}): {e}，等待 {wait:.0f}s")
                    time.sleep(wait)
                    continue
                raise ServerError(f"网络错误: {e}") from e

        raise ServerError(
            f"API 调用失败 (已重试 {self.config.max_retries} 次): {last_error}"
        )

    @staticmethod
    def _handle_error(resp: requests.Response, endpoint: str) -> None:
        status = resp.status_code
        try:
            err_body = resp.json()
            err_msg = err_body.get("error", {}).get("message", resp.text[:200])
        except (ValueError, AttributeError):
            err_msg = resp.text[:200]

        if status == 400:
            raise InvalidRequestError(f"请求参数错误: {err_msg}")
        elif status in (401, 403):
            raise AuthError(f"认证失败: {err_msg}")
        elif status == 404:
            raise ModelNotFoundError(f"接口不存在: {endpoint} - {err_msg}")
        elif status == 429:
            raise RateLimitError(f"请求频率超限: {err_msg}")
        elif status >= 500:
            raise ServerError(f"服务器错误 ({status}): {err_msg}")
        else:
            raise ServerError(f"未知错误 ({status}): {err_msg}")

    @staticmethod
    def _encode_image(image_path: str) -> Tuple[str, str]:
        """将图片编码为 base64

        Returns:
            (mime_type, base64_data)
        """
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        size_mb = path.stat().st_size / (1024 * 1024)
        if size_mb > 20:
            raise ValueError(f"图片过大 ({size_mb:.1f}MB)，请压缩后重试")

        suffix = path.suffix.lower()
        mime_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        mime = mime_map.get(suffix, "image/png")

        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")

        return mime, b64

    def close(self):
        """清理所有 Session"""
        if self._chat_session:
            self._chat_session.close()
        if self._multimodal_session:
            self._multimodal_session.close()
        if self._image_session:
            self._image_session.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


# ─── 向后兼容别名 ───────────────────────────────────────────

class SenseNovaClient(InfographicsClient):
    """向后兼容的别名类

    保留 SenseNovaClient 名称以便旧代码继续使用。
    推荐使用新的 InfographicsClient。
    """
    def __init__(self, *args, **kwargs):
        import warnings
        warnings.warn(
            "SenseNovaClient 已重命名为 InfographicsClient，请使用新名称。",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)


def test_connection(config: Config, verbose: bool = True) -> Tuple[bool, str]:
    """测试 API 连通性

    Args:
        config: 配置对象
        verbose: 是否打印详细信息

    Returns:
        (是否成功, 消息)
    """
    client = InfographicsClient(config)
    try:
        result = client.multimodal_analyze(
            "Respond with exactly: OK",
            system_prompt="You are a helpful assistant.",
            max_tokens=20,
        )
        if verbose:
            logger.info("API 连通性测试通过")
            logger.info(f"  对话模型: {config.chat.model} @ {config.chat.base_url}")
            logger.info(f"  多模态模型: {config.multimodal.model} @ {config.multimodal.base_url}")
            logger.info(f"  生图模型: {config.image.model} @ {config.image.base_url}")
        return True, "API 连接成功"
    except Exception as e:
        if verbose:
            logger.error(f"API 连接失败: {e}")
        return False, str(e)
    finally:
        client.close()