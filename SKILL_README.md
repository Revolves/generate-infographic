# generate-infographic — Claude Code 技能

> 通过多轮问答收集信息图需求，自动调用 AI 生成专业信息图

## 简介

`generate-infographic` 是一个 Claude Code 技能（slash command），通过 8 轮智能问答收集用户需求后，自动调度 AI 模型完成多模态分析和信息图生成。

## 安装

### 1. 将技能添加到项目

将以下文件复制到你的项目目录中：

```
.claude/
├── skills/
│   └── generate-infographic.md   # 技能定义
└── settings.local.json           # 技能注册
```

### 2. 安装 Python 依赖

```bash
git clone https://github.com/Revolves/generate-infographic.git
cd generate-infographic
pip install -e .
```

> 注意：当前仅支持从源码安装，暂未发布到 PyPI。

### 3. 配置 API Key

在项目根目录创建 `.env` 文件：

```ini
SENSENOVA_API_KEY=your_api_key_here
```

也可以独立配置三种模型：

```ini
# 对话模型（分析需求）
CHAT_API_KEY=sk-xxx
CHAT_BASE_URL=https://api.openai.com/v1
CHAT_MODEL=gpt-4o

# 多模态模型（图片理解、质量评估）
MULTIMODAL_API_KEY=sk-xxx
MULTIMODAL_BASE_URL=https://api.sensenova.cn/v1
MULTIMODAL_MODEL=sensenova-6.7-flash-lite

# 生图模型（信息图生成）
IMAGE_API_KEY=sk-xxx
IMAGE_BASE_URL=https://api.sensenova.cn/v1
IMAGE_MODEL=sensenova-u1-fast
```

## 使用方法

### 在 Claude Code 中启动

```bash
claude
# 进入项目目录后输入：
/generate-infographic
```

### 工作流程

技能会引导你完成以下步骤：

**阶段一：需求收集（8 轮问答）**

| 轮次 | 问题 | 说明 |
|------|------|------|
| 1 | 主题与目的 | 信息图的核心主题和目标 |
| 2 | 目标受众 | 读者群体和知识水平 |
| 3 | 关键数据与内容 | 需要展示的数据和要点 |
| 4 | 叙事结构 | 信息组织方式（时间线/对比/中心发散等） |
| 5 | 视觉风格与配色 | 设计风格和颜色偏好 |
| 6 | 布局与尺寸 | 图片尺寸和内容区块数量 |
| 7 | 品牌元素 | 品牌名称、Logo、品牌色等 |
| 8 | 输出格式与补充 | 特殊要求或参考图片 |

**阶段二：联网数据补全**

系统会自动使用 WebSearch 检索缺失的数据，并询问你是否采纳。

**阶段三：预览与确认**

1. 系统运行多模态分析，构建生成提示词
2. 展示分析结果和提示词供你预览
3. 你可以确认生成，或直接提出修改意见

### 修改与迭代

不满意结果？直接说修改意见，系统会自动更新需求并重新预览：

```
"把颜色改成蓝色调，标题放大一些"
"增加一个对比图表"
"字体改成更正式的风格"
```

可以无限循环修改，直到满意为止。

## 文件说明

| 文件 | 说明 |
|------|------|
| `.claude/skills/generate-infographic.md` | 技能定义文件（核心） |
| `.claude/settings.local.json` | 技能注册配置 |
| `.env` | API Key 配置 |
| `requirements.json` | 技能输出的需求文件 |

## 环境变量

| 变量 | 用途 | 默认值 |
|------|------|--------|
| `SENSENOVA_API_KEY` | API Key（退避基准） | — |
| `CHAT_MODEL` | 对话模型 | `sensenova-6.7-flash-lite` |
| `MULTIMODAL_MODEL` | 多模态模型 | `sensenova-6.7-flash-lite` |
| `IMAGE_MODEL` | 生图模型 | `sensenova-u1-fast` |
| `IMAGE_SIZE` | 默认图片尺寸 | `2752x1536` |

## 注意事项

- 生图模型（如 `sensenova-u1-fast`）返回的图片 URL 有效期 1 小时，请及时下载
- 自优化循环最多 10 轮，自动评估生成质量并改进
- 复杂内容会自动拆分为多张子图分别生成

## 技术要求

- Python 3.10+
- Claude Code CLI
- SenseNova API Key（或兼容的 OpenAI API Key）