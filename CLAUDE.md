# Infographics Agent

基于 AI 多模态模型的信息图生成 Agent。支持独立配置对话模型、多模态模型和生图模型的 URL 和 API Key。

## 架构

- **`/generate-infographic` skill**: Claude Code 技能，通过多轮问答收集用户需求
- **`infographics_agent` 包**: Python 包，调用 AI API 进行多模态分析和信息图生成

### 三模型架构

| 模型 | 用途 | 默认值 |
|------|------|--------|
| 对话模型 (Chat) | 纯文本对话、需求分析 | `sensenova-6.7-flash-lite` |
| 多模态模型 (Multimodal) | 图文分析、质量评估 | `sensenova-6.7-flash-lite` |
| 生图模型 (Image) | 信息图生成 | `sensenova-u1-fast` |

## 使用方法

### 1. 安装

```bash
pip install -e .
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，填写配置：
```
SENSENOVA_API_KEY=your_api_key_here
```

### 3. 收集需求

在 Claude Code 中运行：
```
/generate-infographic
```
按照引导回答 8 轮问题，完成需求收集。

### 4. 生成信息图

```bash
python -m infographics_agent -r requirements.json
```

或通过 Claude Code 自动调度。

## 文件结构

```
├── .claude/skills/
│   └── generate-infographic.md  # 多轮需求收集技能
├── infographics_agent/          # Python 包
│   ├── __init__.py              # 版本号 + 导出
│   ├── __main__.py              # python -m 入口
│   ├── config.py                # 三模型独立配置
│   ├── client.py                # 多 Provider API 客户端
│   ├── agent.py                 # 主编排器
│   ├── cli.py                   # CLI 入口
│   ├── exceptions.py            # 自定义异常
│   └── prompt_templates.py      # 提示词模板
├── src/                         # 向后兼容 shim
├── output/                      # 生成图片输出目录
├── .env                         # API Key 配置
├── pyproject.toml               # 构建配置
├── README.md                    # 中文文档
├── README_EN.md                 # 英文文档
└── LICENSE                      # MIT License
```

## 工作流

1. `/generate-infographic` → 多轮问答收集需求 → `requirements.json`
2. `python -m infographics_agent --preview -r requirements.json` → 多模态分析预览
3. 确认后 `python -m infographics_agent -r requirements.json` → 生成图片（含自优化）

## 独立配置各模型

```ini
# 示例：对话用 GPT-4o，生图用 SenseNova
CHAT_API_KEY=sk-openai-xxx
CHAT_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o

IMAGE_API_KEY=sk-sensenova-xxx
IMAGE_BASE_URL=https://api.sensenova.cn/v1
IMAGE_MODEL=sensenova-u1-fast
```