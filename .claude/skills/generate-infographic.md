---
name: generate-infographic
description: "Multi-round Q&A infographic requirement collection — deep analysis + web search + prompt preview & confirmation / 多轮问答收集信息图需求 — 深度收集 + 联网补全 + 提示词预览确认"
---

# generate-infographic — Infographic Requirement Collection & Generation Skill
# generate-infographic — 智能信息图需求收集与生成技能

<!--
=== English Overview ===
This Claude Code skill guides users through a structured workflow to generate professional infographics.
It consists of three phases:
  Phase 1: Deep requirement collection (8 rounds of Q&A with smart follow-ups)
  Phase 2: Web search data completion
  Phase 3: Prompt preview, confirmation, and generation

=== 中文概述 ===
本技能引导用户通过结构化流程生成专业信息图，包含三个阶段：
  阶段一：深度需求收集（8~12轮问答，含智能追问）
  阶段二：联网数据补全
  阶段三：提示词预览、确认与生成
-->

You are executing an **infographic requirement collection and generation task**. The workflow has three phases:

- **Phase 1 · Deep Requirement Collection (8~12 rounds)** — One topic at a time, with smart follow-ups
- **Phase 2 · Web Search Data Completion** — Use WebSearch to fill in missing data
- **Phase 3 · Prompt Preview & Confirmation** — Run analysis → show prompt → user confirms → generate

> ⚠️ **Rules / 规则**:
> - **Ask one question at a time**, wait for the user's answer before proceeding / **每次只问一个主要问题**，等用户回答后再进行下一步
> - Decide whether to follow up based on the user's answer, don't mechanically ask all follow-ups / 根据用户的回答内容决定是否追问，不要机械地全部追问
> - At most 2 meaningful follow-ups per topic / 有参考价值的追问不超过 2 个，避免冗长
> - Communicate in Chinese throughout / 全程使用中文交流

---

## Phase 1: Deep Requirement Collection / 阶段一：深度需求收集

Ask questions one by one in order. Each topic has a **core question** and **optional follow-ups** — only ask follow-ups when the user's answer is vague or there's room to go deeper.

按顺序逐一提问。每个主题都有**核心问题**和**可选追问**——追问仅在用户回答含糊或可深入时触发。

### Q1: Topic & Purpose / 第 1 题：主题与目的

<!-- Record field: `purpose` -->

**Core question / 核心问题**：
"您好！我来帮您设计一张专业的信息图 🎨

首先，**这张信息图的核心主题是什么？主要目的是什么？**
比如：产品功能介绍、行业数据报告、流程步骤说明、品牌宣传展示、科普教育等。

请详细描述一下——越具体，我越能帮您做得精准。如果有相关的背景资料，也欢迎告诉我。"

**Record field / 记录字段**: `purpose`

**Follow-up rule / 追问规则**：If the user's answer is too vague (e.g., just "promotion" or "show data"), ask:
"能具体说一下您想传达的核心信息或关键卖点吗？比如最想让读者记住的一个点是什么？"

---

### Q2: Target Audience / 第 2 题：目标受众

<!-- Record field: `audience` -->

**Core question / 核心问题**：
"了解了！**谁会是这张信息图的主要读者？** 这决定了信息密度、用词风格和视觉调性。

比如：
- 公司高管 / 投资人 → 需要宏观结论和关键数据
- 技术团队 → 可以包含专业术语和技术细节
- 终端用户 / 大众消费者 → 需要通俗易懂、视觉吸引力强
- 行业峰会 / 展会观众 → 需要高端大气、品牌感强

您的主要受众是哪类人群？他们对这个主题的了解程度如何？"

**Record field / 记录字段**: `audience`

**Follow-up rule / 追问规则**：If the user hasn't mentioned knowledge level, ask:
"他们对这个话题的了解程度怎么样？（初学者 / 有一定了解 / 专家级别）"

---

### Q3: Key Data & Content / 第 3 题：关键数据与内容

<!-- Record field: `key_data` -->

**Core question / 核心问题**：
"好的！**您希望在这张信息图中展示哪些核心数据或内容？**

请列出关键信息点、数据指标或需要突出的重点。最好能提供**具体的数据和数字**——精确的数据会让信息图更有说服力。

例如：
- ❌ 'AI 行业增长很快'
- ✅ '2025 年全球 AI 市场规模达 $244B，年增长率 36.6%'

请逐条列出您想展示的内容："

**Record field / 记录字段**: `key_data`

**Follow-up rules / 追问规则**：
- If the user mentions statistics, trends, or comparisons without specific numbers → mark as "needs web search completion", use WebSearch in Phase 2
  / 如果用户提到统计数据、行业趋势、比较数据但没有给出具体数字 → 记录为「需联网补全」，后续在阶段二用 WebSearch 检索
- If the user lists fewer than 3 items → ask: "还有没有其他想补充展示的信息点？信息图一般需要 3~6 个核心信息区块才能显得充实。"

---

### Q4: Narrative Structure / 第 4 题：叙事结构与信息层级

<!-- Record field: `narrative` -->

**Core question / 核心问题**：
"好素材！**您希望信息图采用什么样的叙事结构或信息流？**

常见的结构有：
- 🏗️ **自上而下**：按重要性递减，最重要的在最上面
- 📖 **时间线**：按时间顺序展示发展历程或步骤
- 🔄 **对比式**：左右/前后对比，突出差异
- 🧩 **问题→解决方案**：先抛出问题，再展示你的解决方案
- 🗺️ **中心发散**：核心主题在中间，分支信息向四周展开

您倾向于哪种方式？或者有自己设想的布局思路？"

**Record field / 记录字段**: `narrative`

**Follow-up rule / 追问规则**：If the user is unsure, suggest:
"根据您之前提到的主题，我建议使用 **[analyze and pick the best structure]** 结构，您觉得怎么样？"

---

### Q5: Visual Style & Colors / 第 5 题：视觉风格与配色

<!-- Record field: `style` -->

**Core question / 核心问题**：
"关于**视觉风格和配色**，您有什么偏好吗？

🎨 **风格选项**：
- 简约现代（留白多、线条干净）
- 科技未来感（深色背景、霓虹蓝紫）
- 商务专业（蓝白灰、稳重）
- 活泼明快（高饱和度彩色、圆润元素）
- 手绘插画风（手写字体、手绘元素）
- 国潮/中国风（传统色彩、中式纹样）
- 极简主义（黑白灰、极简排版）

🎭 **希望传达的情绪**：专业 / 温暖 / 清新 / 高端 / 活力 / 权威

🎨 **主色调偏好**：如果有喜欢的颜色请告诉我"

**Record field / 记录字段**: `style`

**Follow-up rules / 追问规则**：
- If the user says "not sure" or "you decide" → recommend 2-3 styles based on their industry/audience
  / 如果用户说"不确定"或"你看着办" → 根据前面收集的行业和受众推荐 2~3 种风格供选择
- If the user provided industry info but no style preference → "{{industry}}类的信息图通常采用{{style}}风格，您觉得合适吗？"

---

### Q6: Layout & Size / 第 6 题：布局与尺寸

<!-- Record field: `layout` -->

**Core question / 核心问题**：
"**您期望的布局尺寸是怎样的？**

📐 **常见尺寸**：
- 竖版 1080×1920（适合手机分享、社交媒体）
- 横版 1920×1080 / 2752×1536（适合展示、网页、印刷）
- 方形 1080×1080 / 2048×2048（适合 Instagram 等社交平台）
- 宽屏 3072×1376（适合宽屏演示）

**大概需要展示几个内容区块？** 3 个左右还是 6 个以上？"

**Record field / 记录字段**: `layout`

---

### Q7: Brand Elements / 第 7 题：品牌元素

<!-- Record field: `brand` -->

**Core question / 核心问题**：
"**这张信息图需要包含品牌元素吗？**

如果有，请提供以下信息：
- 🏢 公司/品牌名称
- 🎯 Logo 文件路径（如果有本地图片，请提供路径）
- 🎨 品牌色（如品牌主色：#0052CC 或提供色值）
- ✏️ 品牌字体
- 📢 品牌 Slogan 或需要突出的标语

如果没有品牌要求，直接说'无'即可，我会用通用设计。"

**Record field / 记录字段**: `brand`

---

### Q8: Output Format & Notes / 第 8 题：输出格式与补充说明

<!-- Record field: `additional_notes` -->

**Core question / 核心问题**：
"最后一个问题！**关于输出还有其他要求吗？**

比如：
- 是否需要特定格式的源文件
- 有没有参考图想让我参考风格（如果有参考图片，请提供路径，我会用多模态模型分析它的设计风格）
- 其他任何补充说明或特殊要求"

**Record field / 记录字段**: `additional_notes`

---

## Phase 2: Web Search Data Completion / 阶段二：联网数据补全

After all 8 questions are answered, check if data completion is needed:

所有 8 个问题回答完毕后，执行数据补全检查：

### Check if `key_data` needs WebSearch completion / 检查用户提供的 `key_data` 是否需要 WebSearch 补全

Use WebSearch if any of the following conditions are met / 如果满足以下任一条件，使用 WebSearch 检索：

1. **User mentioned industry/market data without specific numbers**
   / **用户提到了行业/市场数据但没有具体数字**
   - E.g., user says "AI industry is growing fast" → search "2025 2026 AI market size growth statistics"
   - E.g., user says "China NEV sales are high" → search "2025 2026 China NEV sales data"

2. **User mentioned trends without supporting data**
   / **用户提到了趋势但没有具体数据支撑**
   - E.g., user says "remote work is becoming more popular" → search "remote work statistics 2025 2026"

3. **User said "find the data for me"**
   / **用户表示"数据由你来找"或"帮我找找相关数据"**

### Search Strategy / 搜索策略

- 1-2 WebSearch calls per data gap, select the most relevant and recent data / 每个信息缺口使用 1~2 次 WebSearch，精选最相关、最新的数据
- Prefer Chinese keywords / 优先使用中文关键词搜索
- Prefer 2025-2026 data / 搜索时间范围：优先搜索 2025-2026 年的数据

### Present Results / 展示补全结果

Organize the searched data and **ask the user if they want to adopt it**:

将搜索到的数据整理后，**询问用户是否要采纳**：
"我查到了以下相关数据可以补充到信息图中：
1. 📊 {{Data point 1 / 数据点 1}}
2. 📊 {{Data point 2 / 数据点 2}}

您希望将这些包含进去吗？或者您有其他想调整的内容？"

Update `key_data` and `additional_notes` based on the user's response.

根据用户的回复，更新 `key_data` 和 `additional_notes` 中的内容。

---

## Phase 3: Prompt Preview & Confirmation / 阶段三：提示词预览与确认

### Step 1: Save Requirements / 保存需求文件

Use the Write tool to save all collected requirements as `requirements.json`:

```json
{
  "purpose": "User's detailed answer / 用户的详细回答",
  "audience": "User's answer about target audience / 用户的详细回答",
  "key_data": "User's key data (with web-completed data) / 用户的详细回答（含联网补全内容）",
  "narrative": "User's narrative structure preference / 用户的叙事结构偏好",
  "style": "User's style preference / 用户的风格偏好",
  "layout": "User's layout requirement (with size) / 用户的布局要求（含尺寸）",
  "brand": "User's brand info / 用户的品牌信息",
  "image_paths": ["Reference image paths if any / 如果有参考图路径则填入"],
  "additional_notes": "User's additional notes / 用户的补充说明"
}
```

### Step 2: Run Analysis Preview / 运行分析预览

Use Bash to run (set timeout to 120 seconds / 设置超时 120 秒)：

```bash
python -m infographics_agent --preview -r requirements.json
```

This runs multimodal analysis and builds the generation prompt, **without actually generating the image**.

这会执行多模态分析并构建生成提示词，**但不实际生成图片**。

### Step 3: Show Prompt to User / 展示提示词给用户

Extract the **analysis results** and **generation prompt** from the output, and present them to the user:

提取输出中的**分析结果**和**生成提示词**，向用户展示预览：

"📋 **Analysis Summary / 分析结果摘要**：
- 主题识别 / Theme: {{分析识别的主题}}
- 建议风格 / Style: {{建议的视觉风格}}
- 布局建议 / Layout: {{建议的布局结构}}

📝 **Generation Prompt / 信息图生成提示词**（将发送给生成模型）：

```
{{展示完整提示词}}
"

🎯 **Please confirm if this prompt meets your expectations / 请您确认这个提示词是否符合您的预期？**

- If **good**, say "确认" or "生成" / 如果**没问题**，说"确认"或"生成"
- If **revision needed**, tell me what to adjust / 如果需要**修改**，直接告诉我具体想调整什么，我来帮您更新

（例如："把颜色改成蓝色调"、"增加一个对比图表"、"字体放大一些"——直接说，不用先喊'修改'）"

### Step 4: Branch Based on User Response / 根据用户回复分流

**Branch A — User Confirms Generation / 用户确认生成**
When the user's reply contains confirmation keywords / 用户回复包含以下确认词时，视为确认：
- 确认 / 生成 / 可以 / 好的 / 行 / 没问题 / 就这样 / Go / Yes / 好 / 不错

→ Run full generation (**with automatic multi-round quality optimization / 含自动多轮质量优化**)：
  ```bash
  python -m infographics_agent -r requirements.json
  ```

  > 🔄 The generation pipeline runs up to 3 rounds of self-improvement:
  > / 生成流程会自动进行最多 3 轮自优化：
  > 1. Generate image → multimodal model evaluates quality → pass = done
  >    / 生成图片 → 多模态模型评估质量 → 通过则结束
  > 2. If not passed, auto-improve the prompt → regenerate → re-evaluate
  >    / 未通过则自动改进提示词 → 重新生成 → 再次评估
  > 3. Until evaluation passes or max rounds reached
  >    / 直到评估通过或达到最大轮次

→ After generation, show results (with self-improvement info) / 生成完成后，展示结果（含自优化信息）：
  ```
  ✅ 信息图生成完成 / Infographic generation complete!
  🔄 自优化 / Self-improvement: Round N passed
  🖼️ 图片已保存至 / Image saved to: {{image path}}
  ```

**Branch B — User Provides Feedback / 用户反馈修改意见**
When the user's reply is natural language feedback (not confirmation keywords), **treat it directly as revision feedback** / 用户回复是自然语言修改意见（非确认词）时，**直接视为修改意见**，无需先喊"修改一下"：

→ **Do NOT manually edit requirements.json / 不要手动编辑 requirements.json**

→ Use the user's original words as feedback, run `--refine` (it auto-updates requirements.json and shows the new prompt) / 将用户的原话作为修改意见，运行 `--refine`（会自动更新 requirements.json 并展示新提示词）：
  ```bash
  python -m infographics_agent --refine --feedback "<user's feedback / 用户的原话>" -r requirements.json
  ```

  > ⚠️ Replace `<user's feedback>` with the actual user input, e.g.:
  > / 将 `<用户的修改意见>` 替换为用户实际说的话，如：
  > ```bash
  > python -m infographics_agent --refine --feedback "把颜色改成蓝色调，增加一个对比图表，字体放大一些" -r requirements.json
  > ```
  > If the feedback contains quotes, use Chinese quotes 「」 or escape them.
  > / 如果反馈内容包含引号，用中文引号「」或转义处理。

→ Extract the **updated requirements summary**, **analysis results**, and **prompt** from the output, show them to the user, and **return to Step 3** for confirmation.

→ 提取输出中的**更新后的需求摘要**、**分析结果**和**提示词**，展示给用户，**再次回到步骤 3 的确认环节**

> 💡 Users can iterate infinitely: give feedback → `--refine` → show new prompt → confirm/re-feedback → ...
> / 用户可无限循环：直接提意见 → `--refine` → 展示新提示词 → 再确认/再提意见 → ...

---

## Use Case Handling / 用例处理

| Scenario / 场景 | Handling / 处理方式 |
|------|----------|
| User provides reference image paths / 用户提供参考图片路径 | Fill into `image_paths`, multimodal model will analyze the style / 填入 `image_paths`，后续多模态模型会分析图片风格 |
| User has no brand requirements / 用户没有品牌要求 | Set `brand` to "无", generate generic design / `brand` 字段设为 "无"，生成通用设计 |
| User is unsure about style / 用户不确定风格 | Recommend 2-3 styles based on industry / 根据行业推荐 2~3 种风格 |
| User data is incomplete / 用户数据不完整 | WebSearch then ask if they want to adopt / WebSearch 检索后询问是否采纳 |
| User wants to modify prompt / 用户想修改提示词 | Collect feedback → `--refine` → re-preview / 收集修改意见 → `--refine` 调用模型修改 → 重新预览 |
| User modifies multiple times / 用户多次修改 | Each loop: feedback → `--refine` → show → confirm / 每次循环：收集意见 → `--refine` → 展示 → 再确认 |
| User skips web search / 用户跳过 websearch | Respect the user's decision, go to Phase 3 / 尊重用户决定，直接进入阶段三 |
| Auto-optimization during generation / 生成时自动优化 | Run automatically up to 3 rounds of "generate → evaluate → improve → regenerate" / run 命令自动执行最多 3 轮「生成→评估→改进→再生」循环 |