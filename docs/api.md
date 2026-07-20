# API 参考

## Config

```python
from infographics_agent import Config, load_config

config = load_config()  # 从 .env 和环境变量加载
```

### 属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `config.chat` | `ModelEndpoint` | 对话模型端点配置 |
| `config.multimodal` | `ModelEndpoint` | 多模态模型端点配置 |
| `config.image` | `ModelEndpoint` | 生图模型端点配置 |
| `config.image_size` | `str` | 默认图片尺寸 |
| `config.request_timeout` | `int` | 请求超时(秒) |
| `config.max_retries` | `int` | 最大重试次数 |
| `config.output_dir` | `str` | 输出目录 |

### ModelEndpoint

```python
from infographics_agent.config import ModelEndpoint

endpoint = ModelEndpoint(
    api_key="sk-xxx",
    base_url="https://api.example.com/v1",
    model="gpt-4o",
)
```

## InfographicsClient

```python
from infographics_agent import InfographicsClient, Config

config = load_config()
client = InfographicsClient(config)

# 多模态分析
result = client.multimodal_analyze(
    text="分析这张图片",
    image_paths=["path/to/image.png"],
    system_prompt="你是一个设计专家",
)

# 纯文本对话
result = client.chat_analyze(
    text="你好",
    system_prompt="你是一个助手",
)

# 生成信息图
images = client.generate_infographic(
    prompt="一张科技感信息图...",
    size="2752x1536",
)

# 下载图片
path = client.download_image(images[0]["url"], "output/")

client.close()  # 或使用 with 语句
```

## InfographicAgent

```python
from infographics_agent import InfographicAgent, load_config

config = load_config()
agent = InfographicAgent(config)

# 预览（仅分析，不生成）
result = agent.analyze_only("requirements.json")

# 完整生成
result = agent.run("requirements.json")

# 根据反馈修改
result = agent.refine_and_preview("requirements.json", "把颜色改成蓝色")

agent.close()  # 或使用 with 语句
```

## 异常处理

```python
from infographics_agent.exceptions import (
    InfographicsError, AuthError, ConfigError,
    RateLimitError, ModelNotFoundError,
    InvalidRequestError, ServerError,
)

try:
    result = agent.run("requirements.json")
except AuthError:
    print("API Key 无效")
except RateLimitError:
    print("请求频率超限，请稍后重试")
except ModelNotFoundError:
    print("模型不存在或已下线")
except ConfigError:
    print("配置错误，请检查 .env 文件")
except InfographicsError as e:
    print(f"其他错误: {e}")
```