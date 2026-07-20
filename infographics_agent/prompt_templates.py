"""提示词模板 - 管理多模态分析和信息图生成的提示词

包含分析提示词、生成提示词、质量评估提示词和自优化提示词。
"""

import json
from itertools import zip_longest
from typing import Any, Dict, List, Optional


# ─── 多模态分析提示词 ───────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """你是一个专业的信息图设计专家。你的任务是基于用户的需求，进行深入分析，提取关键信息以指导信息图生成。

请从以下维度进行分析：

1. **主题与目的**: 信息图的核心主题是什么？要达到什么目的？（教育、宣传、数据展示、流程说明等）
2. **核心信息**: 需要传达的关键数据和信息要点
3. **目标受众**: 受众是谁？他们的知识水平和兴趣点是什么？
4. **视觉风格**: 建议的配色方案、字体风格、整体调性（专业/活泼/简约/科技感等）
5. **布局建议**: 信息层级结构，如何组织内容区块。**请用空间位置描述布局（如：左侧区块展示...、右侧区域展示...、中央放置...），而非抽象概念**
6. **数据可视化**: 适合使用的图表类型（柱状图、饼图、时间线、流程图等）
7. **品牌元素**: 是否需要包含 Logo、品牌色等

请以结构化的 JSON 格式输出分析结果，包含以上所有维度。"""


def build_analysis_prompt(requirements: Dict[str, Any]) -> str:
    """构建多模态分析提示词

    Args:
        requirements: 用户需求字典（来自 generate-infographic skill）

    Returns:
        分析提示词
    """
    sections = [
        "## 用户需求分析请求\n",
        "请分析以下信息图需求，并给出专业的设计建议：\n",
    ]

    # 逐项添加需求
    field_labels = {
        "purpose": "📋 主题与目的",
        "audience": "👥 目标受众",
        "key_data": "📊 关键数据/内容",
        "narrative": "📖 叙事结构",
        "style": "🎨 风格与配色偏好",
        "brand": "🏷️ 品牌信息",
        "layout": "📐 布局偏好",
        "output_format": "📏 输出格式要求",
    }

    for key, label in field_labels.items():
        if key in requirements and requirements[key]:
            sections.append(f"**{label}**: {requirements[key]}\n")

    # 额外说明
    if "additional_notes" in requirements and requirements["additional_notes"]:
        sections.append(f"**📝 补充说明**: {requirements['additional_notes']}\n")

    sections.append(
        "\n请输出结构化的分析结果，包含主题目的、核心信息、视觉风格、布局建议等维度。"
    )

    return "".join(sections)


# ─── 信息图生成提示词 ───────────────────────────────────────

INFOGRAPHIC_PROMPT_TEMPLATE_V2 = """请生成一张专业的中文信息图。

以{color_scheme}为主色调，采用{style_description}风格，整体{layout_description}

图中需要展示以下全部内容（请完整渲染以下所有文字，不要省略任何内容）：

【{theme}】

{content}

{extra_info}

设计要求：
- 完整渲染以上列出的全部文字内容，确保文字清晰可读
- 配色严格遵循指定方案
- 整体设计专业美观"""


def build_split_prompts(analysis: Dict[str, Any]) -> List[str]:
    """将分析数据拆分为多个子提示词，每张子图只展示部分内容

    拆分策略（以数据中的标记为界）：
    1. 概览：园区概况（开园时间、占地、投资、定位）+ 品牌/受众
    2. 七大园区：7 个园区名称+代表项目
    3. 游园攻略：游玩建议、交通、餐饮等

    Returns:
        子提示词列表（每个元素是一张子图的完整提示词）
    """
    # 公共部分（所有子图共享）
    color_raw = analysis.get("color_scheme", [])
    if isinstance(color_raw, list):
        color_text = "、".join(str(c).strip() for c in color_raw if c)
    else:
        color_text = str(color_raw)
    style_text = _format_text(analysis.get("style_description", analysis.get("visual_style", "专业简洁")))

    # 获取全体数据文本
    data_text = _format_text(analysis.get("data_points", analysis.get("core_info", "")))

    # 按关键标记拆分
    overview = ""
    parks = ""
    guide = ""

    # 尝试按标记拆分
    parts = data_text.split("游园攻略:")
    if len(parts) >= 2:
        guide_section = "游园攻略:" + parts[1]
        rest = parts[0]
    else:
        guide_section = ""
        rest = data_text

    parts2 = rest.split("七大主题园区:")
    if len(parts2) >= 2:
        parks_section = "七大主题园区:" + parts2[1]
        overview_section = parts2[0].strip()
    else:
        parks_section = ""
        overview_section = rest.strip()

    # 如果拆出来的段落太短，用原始数据
    if len(parks_section) < 20:
        parks_section = data_text
        overview_section = analysis.get("theme", str(analysis.get("purpose", "")))
        guide_section = ""

    # ─── 子图1：概览卡片 ───
    extra_parts = []
    audience = analysis.get("audience", "")
    if audience and str(audience).strip() not in ("大众", "大众消费者"):
        extra_parts.append(f"目标受众：{_format_text(audience)}")
    brand = analysis.get("brand_info", analysis.get("brand", ""))
    if brand and str(brand).strip() not in ("无", ""):
        extra_parts.append(f"品牌信息：{_format_text(brand)}")
    extra_info = "\n".join(extra_parts)

    overview_prompt = INFOGRAPHIC_PROMPT_TEMPLATE_V2.format(
        theme=analysis.get("theme", analysis.get("purpose", "信息图")),
        style_description=style_text,
        layout_description="居中标题+关键数据卡片布局，清晰展示核心数据",
        color_scheme=color_text or "专业蓝",
        content=overview_section if overview_section else "核心数据展示",
        extra_info=extra_info,
    )

    # ─── 子图2：七大园区 ───
    parks_prompt = INFOGRAPHIC_PROMPT_TEMPLATE_V2.format(
        theme="七大主题园区",
        style_description=style_text,
        layout_description="三行网格布局，每行2-3个园区卡片，位置固定：第一行左起：哈利·波特的魔法世界、变形金刚基地、功夫熊猫盖世之地；第二行左起：侏罗纪世界努布拉岛、小黄人乐园；第三行左起：好莱坞、未来水世界。每个卡片含园区名和代表项目，信息对应准确不混淆",
        color_scheme=color_text or "专业蓝",
        content=parks_section if parks_section else "七大园区介绍",
        extra_info="",
    )

    # ─── 子图3：游园攻略 ───
    guide_prompt = INFOGRAPHIC_PROMPT_TEMPLATE_V2.format(
        theme="游园攻略",
        style_description=style_text,
        layout_description="清单/卡片布局，按类别展示游玩建议、交通、餐饮等实用信息",
        color_scheme=color_text or "专业蓝",
        content=guide_section if guide_section else "实用游玩信息",
        extra_info="",
    )

    return [overview_prompt, parks_prompt, guide_prompt]


def build_infographic_prompt(analysis: Dict[str, Any]) -> str:
    """根据分析结果构建信息图生成提示词（正向指令风格）

    Args:
        analysis: 多模态分析结果（结构化字典）

    Returns:
        信息图生成提示词
    """
    # 合并颜色方案为文本
    color_raw = analysis.get("color_scheme", [])
    if isinstance(color_raw, list):
        color_text = "、".join(str(c).strip() for c in color_raw if c)
    else:
        color_text = str(color_raw)

    # 合并所有内容为一个内容块
    data_content = analysis.get("data_points", analysis.get("core_info", []))
    text_content = analysis.get("text_content", data_content)
    content_parts = [_format_text(data_content)]
    extra_notes = str(text_content).strip()
    if extra_notes and extra_notes != _format_text(data_content).strip():
        content_parts.append("")
        content_parts.append(extra_notes)
    merged_content = "\n".join(content_parts)

    # 额外信息合并
    extra_parts = []
    audience = analysis.get("audience", "")
    if audience and str(audience).strip() not in ("大众", "大众消费者"):
        extra_parts.append(f"目标受众：{_format_text(audience)}")
    brand = analysis.get("brand_info", analysis.get("brand", ""))
    if brand and str(brand).strip() not in ("无", ""):
        extra_parts.append(f"品牌信息：{_format_text(brand)}")
    extra_info = "\n".join(extra_parts)

    return INFOGRAPHIC_PROMPT_TEMPLATE_V2.format(
        theme=analysis.get("theme", analysis.get("purpose", "信息图")),
        style_description=_format_text(
            analysis.get("style_description", analysis.get("visual_style", "专业简洁"))
        ),
        layout_description=_format_text(
            analysis.get("layout_description", analysis.get("layout", "自上而下的信息层级"))
        ),
        color_scheme=color_text or "专业蓝",
        content=merged_content,
        extra_info=extra_info,
    )


def _extract_color_scheme(analysis: Dict[str, Any]) -> Optional[List[str]]:
    """从 style_description 等字段中提取配色方案"""
    for key in ["style_description", "visual_style"]:
        val = analysis.get(key)
        if isinstance(val, str) and ("色" in val or "配色" in val or "色调" in val):
            lines = val.split("\n")
            colors = [l.split(":", 1)[1].strip() for l in lines if "色" in l and ":" in l]
            if colors:
                return colors
    return None


def _format_list(items: Any) -> str:
    """格式化列表为文本"""
    if isinstance(items, list):
        return "\n".join(f"- {_format_value(item)}" for item in items if item)
    return _format_value(items)


def _format_text(text: Any) -> str:
    """格式化文本内容"""
    if isinstance(text, list):
        return "\n".join(_format_value(t) for t in text)
    return _format_value(text)


def _format_value(value: Any, indent: int = 0) -> str:
    """将任意值格式化为可读文本（支持嵌套 dict/list）

    Args:
        value: 要格式化的值
        indent: 缩进层级

    Returns:
        格式化后的文本
    """
    prefix = "  " * indent
    if isinstance(value, dict):
        lines = []
        for k, v in value.items():
            formatted_v = _format_value(v, indent + 1)
            if "\n" in formatted_v:
                lines.append(f"{prefix}- {k}:\n{formatted_v}")
            else:
                lines.append(f"{prefix}- {k}: {formatted_v}")
        return "\n".join(lines)
    elif isinstance(value, list):
        return "\n".join(f"{prefix}- {_format_value(v, indent)}" for v in value if v)
    else:
        return str(value)


# ─── 需求补全提示词 ───────────────────────────────────────

REQUIREMENT_REFINE_PROMPT = """基于以下分析结果，请生成一个更加精确、详细的信息图生成描述：

{analysis_json}

请将以上分析转化为一个适用于信息图生成模型的详细提示词，要求：
1. 描述完整的视觉布局和构图
2. 指定精确的配色方案和颜色代码
3. 描述每个区块的内容和位置
4. 包含所有文本内容的确切措辞
5. 明确视觉风格和设计调性
"""


def build_refined_prompt(analysis_json: str) -> str:
    """构建精炼提示词

    Args:
        analysis_json: 分析结果的 JSON 字符串

    Returns:
        精炼提示词
    """
    return REQUIREMENT_REFINE_PROMPT.format(analysis_json=analysis_json)


# ─── 需求修改提示词 ───────────────────────────────────────

REQUIREMENT_REFINEMENT_SYSTEM_PROMPT = """你是一个专业的信息图需求分析师。用户对之前的需求提出了修改意见，请根据修改意见**更新完整的 requirements JSON**。

## 规则
1. 保持未修改的字段不变
2. 只修改用户要求调整的部分
3. 如果修改意见涉及数据/数字，直接融入对应字段
4. 输出**完整的 JSON 对象**，包含所有字段

## 输出格式要求
直接输出 JSON，不需要其他解释文字。JSON 必须包含以下字段：
- purpose: 主题与目的
- audience: 目标受众
- key_data: 关键数据与内容（多条用 \n 分隔）
- narrative: 叙事结构
- style: 视觉风格与配色
- layout: 布局与尺寸
- brand: 品牌元素
- image_paths: 图片路径列表（无则为空数组）
- additional_notes: 补充说明"""


def build_refinement_prompt(requirements: Dict[str, Any], feedback: str) -> str:
    """构建需求修改提示词

    Args:
        requirements: 当前的需求字典
        feedback: 用户的修改意见

    Returns:
        修改提示词
    """
    current_json = json.dumps(requirements, ensure_ascii=False, indent=2)
    return f"""## 当前需求

```json
{current_json}
```

## 用户修改意见

{feedback}

## 任务

请根据用户的修改意见，输出更新后的完整 requirements JSON。保持未修改的字段不变。"""


# ─── 质量评估与自优化提示词 ───────────────────────────────────

QUALITY_EVALUATION_SYSTEM_PROMPT = """你是一个专业的信息图质量审核专家。你的任务是基于用户需求和生成提示词，对生成的图片进行质量评估。

请从以下维度严格评估：

1. **内容完整性**（最重要）：是否包含了所有需求中要求展示的信息？有没有遗漏关键数据或板块？
2. **视觉质量与设计**：设计是否专业、清晰？字体是否可读？是否有足够视觉吸引力？
3. **布局与结构**：布局是否符合要求的结构（如中心发散、自上而下等）？信息层级是否清晰？
4. **色彩与风格**：是否遵循了指定的配色方案和视觉风格？风格调性是否匹配？
5. **文字准确性**：文字是否清晰可读？是否有错别字或排版问题？

## 评分标准
- 9-10分：优秀，完全符合需求
- 7-8分：良好，基本符合但有改进空间
- 5-6分：一般，有明显不足需要改进
- 0-4分：不合格，需要大幅修改

## 输出要求
必须输出 JSON 格式（不要其他文字），格式如下：
{
  "pass": true/false,
  "score": 0-10,
  "summary": "一句话总结质量",
  "strengths": ["优点1", "优点2"],
  "issues": ["问题1", "问题2"],
  "improvements": ["改进建议1", "改进建议2"]
}

pass 的判断标准：
- score >= 7 AND 没有严重的内容遗漏 → pass = true
- 有关键信息缺失或 score < 7 → pass = false"""


def build_quality_evaluation_prompt(requirements: Dict[str, Any], prompt: str, eval_scope: str = "") -> str:
    """构建质量评估提示词

    Args:
        requirements: 原始需求
        prompt: 信息图生成提示词
        eval_scope: 评估范围描述（子图评估时使用）

    Returns:
        评估提示词
    """
    req_text = json.dumps(requirements, ensure_ascii=False, indent=2)
    scope_note = ""
    if eval_scope:
        scope_note = f"\n⚠️ 注意：这是一张子图，只展示【{eval_scope}】相关内容。\n请仅评估此范围内内容的完整性和质量，不要因为缺少其他板块内容而扣分。\n"
    return f"""请评估这张信息图的质量。{scope_note}
## 用户原始需求
```json
{req_text}
```

## 用于生成的提示词
{prompt}

## 评估要求
请逐项检查内容完整性、视觉质量、布局结构、色彩风格和文字准确性，然后输出 JSON 格式的评估结果。"""


def build_improvement_prompt(
    analysis: Dict[str, Any], issues: List[str], improvements: List[str]
) -> str:
    """根据评估反馈修改分析数据，然后重建提示词

    Args:
        analysis: 多模态分析结果（结构化字典）
        issues: 评估中发现的问题列表
        improvements: 改进建议列表

    Returns:
        改进后的提示词
    """
    # 浅拷贝分析数据，不修改原始 dict
    new_analysis = dict(analysis)

    if not issues:
        return build_infographic_prompt(new_analysis)

    issues_text = " ".join(issues)
    improvements_text = " ".join(improvements)

    # --- 文字错乱/乱码 → 在风格描述中自然加入精度要求 ---
    if any(w in issues_text for w in ["错别字", "乱码", "错字", "错误", "typo", "garbled"]):
        style = str(new_analysis.get("style_description", ""))
        if "100%准确" not in style:
            new_analysis["style_description"] = style + "，所有文字必须100%准确，无错别字无乱码"

    # --- 内容重复 → 去重 + 强化布局唯一性 ---
    if any(w in issues_text for w in ["重复", "冗余", "duplicate", "redundant"]):
        dp = new_analysis.get("data_points", "")
        if isinstance(dp, str):
            lines = dp.split("\n")
            seen: set = set()
            deduped = []
            for line in lines:
                stripped = line.strip().rstrip(".")
                if stripped and stripped not in seen:
                    seen.add(stripped)
                    deduped.append(line)
                elif not stripped:
                    deduped.append(line)
            new_analysis["data_points"] = "\n".join(deduped)
        layout = str(new_analysis.get("layout_description", ""))
        if "每个板块只出现一次" not in layout:
            new_analysis["layout_description"] = layout + "，每个板块只出现一次，位置固定"

    # --- 布局混乱 → 强化对齐和间距 ---
    if any(w in issues_text for w in ["布局", "混乱", "排版", "layout", "messy", "cluttered"]):
        layout = str(new_analysis.get("layout_description", ""))
        if "对齐规范" not in layout:
            new_analysis["layout_description"] = layout + "，对齐规范，间距均匀，不重叠"

    # --- 信息缺失 → 充实数据 ---
    if any(w in issues_text for w in ["缺失", "遗漏", "不完整", "missing", "incomplete"]):
        tc = new_analysis.get("text_content", "")
        dp = new_analysis.get("data_points", "")
        if not tc or len(str(tc)) < len(str(dp)):
            new_analysis["text_content"] = dp

    # --- 信息错位（园区名与项目不对应）→ 强化配对 ---
    if any(w in issues_text for w in ["混乱", "错位", "对应", "混淆", "mismatch", "wrong"]):
        layout = str(new_analysis.get("layout_description", ""))
        if "信息对应准确" not in layout:
            new_analysis["layout_description"] = layout + "，园区名称与项目信息对应准确，不混淆"

    # --- 英文内容 → 强调纯中文 ---
    if any(w in issues_text for w in ["英文", "english", "must fix"]):
        style = str(new_analysis.get("style_description", ""))
        if "纯中文" not in style:
            new_analysis["style_description"] = style + "，纯中文信息图，无英文"

    # 从修改后的分析数据重建提示词
    return build_infographic_prompt(new_analysis)


def _strip_previous_improvements(prompt: str) -> str:
    """去除提示词中之前轮次叠加的改进指令，只保留原始生成提示词部分

    Args:
        prompt: 可能包含多次叠加改进指令的提示词

    Returns:
        清理后的基础提示词
    """
    for marker in ["\n## 改进要求", "\n## 设计说明", "\n## 视觉设计要求（重要）", "\n## Previous Generation Issues (MUST FIX)"]:
        idx = prompt.find(marker)
        if idx >= 0:
            return prompt[:idx].rstrip()
    return prompt