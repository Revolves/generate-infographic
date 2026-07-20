# Infographics Agent

AI-powered infographics generation tool. Supports independent configuration of chat, multimodal, and image generation models.
基于 AI 多模态模型的信息图生成工具，支持独立配置对话模型、多模态模型和生图模型。

## Architecture / 架构

- **`/generate-infographic` skill**: Claude Code skill for multi-round requirement collection
- **`infographics_agent` package**: Python package for AI API calls and infographic generation

### Three-Model Architecture / 三模型架构

| Model / 模型 | Purpose / 用途 | Default / 默认值 |
|------|------|--------|
| Chat (对话模型) | Text analysis, conversation | `sensenova-6.7-flash-lite` |
| Multimodal (多模态模型) | Image understanding, quality eval | `sensenova-6.7-flash-lite` |
| Image (生图模型) | Infographic generation | `sensenova-u1-fast` |

## Quick Start / 快速开始

```bash
# Install / 安装
pip install -e .

# Configure / 配置 .env with API key
# SENSENOVA_API_KEY=your_api_key_here

# Run the skill / 运行技能
# /generate-infographic
```

## Skill Workflow / 技能工作流

1. `/generate-infographic` → Multi-round Q&A → `requirements.json`
2. `python -m infographics_agent --preview -r requirements.json` → Preview analysis
3. Confirm → `python -m infographics_agent -r requirements.json` → Generate

## Independent Model Configuration / 独立配置各模型

```ini
# Example: chat uses GPT-4o, image generation uses SenseNova
CHAT_API_KEY=sk-openai-xxx
CHAT_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o

IMAGE_API_KEY=sk-sensenova-xxx
IMAGE_BASE_URL=https://api.sensenova.cn/v1
IMAGE_MODEL=sensenova-u1-fast
```

## Project Structure / 文件结构

```
├── .claude/skills/
│   └── generate-infographic.md  # Claude Code skill (bilingual)
├── infographics_agent/          # Python package
├── src/                         # Backward compat shims
├── tests/                       # Test suite
├── docs/                        # Documentation
├── examples/                    # Usage examples
├── pyproject.toml               # Build config
├── README.md                    # Documentation
└── LICENSE                      # MIT License
```