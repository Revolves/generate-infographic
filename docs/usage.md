# 使用指南

## CLI 命令参考

### 基本命令

```bash
python -m infographics_agent [OPTIONS]
```

### 参数

| 参数 | 简写 | 说明 |
|------|------|------|
| `--requirements` | `-r` | 需求 JSON 文件路径 (默认: `requirements.json`) |
| `--test` | | 仅测试 API 连通性 |
| `--preview` | | 预览模式：仅分析，不生成图片 |
| `--refine` | | 修改模式：根据反馈修改需求后重新预览 |
| `--feedback` | | 用户的修改意见（与 `--refine` 配合） |
| `--env` | | `.env` 文件路径 |
| `--output` | | 输出目录 |
| `--verbose` | `-v` | 输出详细日志 |

### 使用示例

```bash
# 测试连通性
python -m infographics_agent --test

# 分析需求并预览提示词
python -m infographics_agent --preview -r requirements.json

# 完整生成
python -m infographics_agent -r requirements.json

# 使用自定义 .env
python -m infographics_agent --env /path/to/.env -r requirements.json

# 指定输出目录
python -m infographics_agent -r requirements.json --output ./output

# 修改需求并重新预览
python -m infographics_agent --refine --feedback "标题改为蓝色，增加数据图表" -r requirements.json

# 详细日志模式
python -m infographics_agent -v -r requirements.json
```

## 需求 JSON 格式

`requirements.json` 包含以下字段：

```json
{
  "purpose": "信息图主题与目的",
  "audience": "目标受众描述",
  "key_data": "关键数据与内容",
  "narrative": "叙事结构偏好",
  "style": "视觉风格与配色偏好",
  "layout": "布局与尺寸要求",
  "brand": "品牌元素信息",
  "image_paths": ["参考图片路径（可选）"],
  "additional_notes": "补充说明（可选）"
}
```

## 工作流

### 完整流程

1. **需求收集** → 使用 Claude Code `/generate-infographic` 技能或手动编写 `requirements.json`
2. **分析预览** → `--preview` 模式，AI 分析需求并构建生成提示词
3. **确认/修改** → 审查提示词，确认生成或提出修改意见
4. **自动生成** → 生成信息图，自动评估质量，多轮改进直到达标
5. **结果输出** → 图片保存到 `output/` 目录

### 修改循环

```
用户反馈 → --refine 模式 → AI 修改需求 → 重新分析 → 新提示词
                                                      ↓
                                              用户确认 → 生成
```