# 配置指南

## 三模型架构

Infographics Agent 支持三种独立的模型端点，每种可来自不同供应商：

```
┌─────────────────────────────────────────────────────────┐
│                   Infographics Agent                     │
├─────────────┬───────────────────┬───────────────────────┤
│  对话模型    │   多模态模型       │   生图模型              │
│  (Chat)     │  (Multimodal)     │  (Image Generation)    │
│             │                   │                       │
│  GPT-4o     │  SenseNova 6.7    │  SenseNova U1 Fast    │
│  Claude     │  GPT-4V           │  DALL-E 3             │
│  文心一言    │  Claude Vision    │  Stable Diffusion     │
└─────────────┴───────────────────┴───────────────────────┘
```

### 各模型用途

| 模型 | 用途 | 要求 |
|------|------|------|
| 对话模型 | 纯文本对话、需求分析（可选） | 仅文本，无需图像输入 |
| 多模态模型 | 参考图片分析、生成质量评估 | 支持图像输入理解 |
| 生图模型 | 信息图生成 | 图像生成能力 |

## 配置方式

### 方式一：环境变量（推荐）

创建 `.env` 文件：

```ini
# === 基础配置（兼容旧版） ===
SENSENOVA_API_KEY=sk-your-key-here
SENSENOVA_BASE_URL=https://api.sensenova.cn/v1

# === 对话模型 ===
CHAT_API_KEY=sk-chat-key
CHAT_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o

# === 多模态模型 ===
MULTIMODAL_API_KEY=sk-multimodal-key
MULTIMODAL_BASE_URL=https://api.sensenova.cn/v1
MULTIMODAL_MODEL=sensenova-6.7-flash-lite

# === 生图模型 ===
IMAGE_API_KEY=sk-image-key
IMAGE_BASE_URL=https://api.sensenova.cn/v1
IMAGE_MODEL=sensenova-u1-fast

# === 共享配置 ===
IMAGE_SIZE=2752x1536
REQUEST_TIMEOUT=120
MAX_RETRIES=3
OUTPUT_DIR=output
```

### 方式二：命令行参数

```bash
# 指定自定义 .env 文件
python -m infographics_agent --env /path/to/.env.custom --preview -r requirements.json

# 指定输出目录
python -m infographics_agent --output ./my_images -r requirements.json
```

## 退避链机制

每个模型配置有退避链，确保向后兼容：

```
CHAT_API_KEY → SENSENOVA_API_KEY
MULTIMODAL_API_KEY → CHAT_API_KEY → SENSENOVA_API_KEY
IMAGE_API_KEY → MULTIMODAL_API_KEY → CHAT_API_KEY → SENSENOVA_API_KEY
```

这意味着：
- 如果只配置了 `SENSENOVA_API_KEY`，三个模型都使用它
- 如果配置了 `CHAT_API_KEY` 但未配置 `MULTIMODAL_API_KEY`，多模态模型使用 `CHAT_API_KEY`
- 如果配置了 `IMAGE_API_KEY`，生图模型使用独立 Key

## 兼容有效尺寸

| 尺寸 | 比例 | 适用场景 |
|------|------|----------|
| `2752x1536` | 16:9 | 横版展示（默认） |
| `1536x2752` | 9:16 | 竖版手机海报 |
| `2048x2048` | 1:1 | 方形（社交平台） |
| `3072x1376` | 21:9 | 宽屏演示 |
| `1664x2496` | 2:3 | 竖版卡片 |
| `2496x1664` | 3:2 | 横版卡片 |
| `1344x3136` | 9:21 | 长竖版 |
| `2560x720` | 32:9 | 超宽屏 |