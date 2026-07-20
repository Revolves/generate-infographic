"""测试 prompt_templates 模块 — 提示词构建"""

import json

from infographics_agent.prompt_templates import (
    ANALYSIS_SYSTEM_PROMPT,
    QUALITY_EVALUATION_SYSTEM_PROMPT,
    REQUIREMENT_REFINEMENT_SYSTEM_PROMPT,
    build_analysis_prompt,
    build_improvement_prompt,
    build_infographic_prompt,
    build_quality_evaluation_prompt,
    build_refinement_prompt,
    build_split_prompts,
)


SAMPLE_REQUIREMENTS = {
    "purpose": "2025年全球AI行业数据报告信息图",
    "audience": "科技公司高管和投资者",
    "key_data": "全球AI市场规模2025年达$244B，年增长率36.6%\n中国AI市场规模2025年达$62B\n主要应用领域：医疗、金融、制造",
    "narrative": "自上而下的信息层级",
    "style": "科技蓝为主色调，简约现代风格",
    "layout": "竖版，顶部标题，中部数据图表，底部总结",
    "brand": "BrandName Inc.",
}


class TestBuildAnalysisPrompt:
    """测试 build_analysis_prompt"""

    def test_basic(self):
        prompt = build_analysis_prompt(SAMPLE_REQUIREMENTS)
        assert "AI行业数据报告" in prompt
        assert "科技公司高管" in prompt
        assert "$244B" in prompt
        assert "BrandName" in prompt

    def test_empty_requirements(self):
        prompt = build_analysis_prompt({})
        assert prompt is not None
        assert len(prompt) > 0

    def test_includes_system_prompt(self):
        assert "信息图设计专家" in ANALYSIS_SYSTEM_PROMPT
        assert "JSON" in ANALYSIS_SYSTEM_PROMPT


class TestBuildInfographicPrompt:
    """测试 build_infographic_prompt"""

    SAMPLE_ANALYSIS = {
        "theme": "2025年全球AI行业数据报告",
        "data_points": "全球AI市场规模2025年达$244B\n年增长率36.6%",
        "style_description": "科技蓝为主色调，简约现代",
        "layout_description": "自上而下，顶部标题，中部数据图表",
        "color_scheme": ["科技蓝", "银色"],
        "audience": "科技公司高管和投资者",
        "brand_info": "BrandName Inc.",
    }

    def test_basic(self):
        prompt = build_infographic_prompt(self.SAMPLE_ANALYSIS)
        assert "全球AI行业数据报告" in prompt
        assert "$244B" in prompt
        assert "科技蓝" in prompt
        assert "BrandName" in prompt

    def test_empty_analysis(self):
        prompt = build_infographic_prompt({})
        assert prompt is not None
        assert len(prompt) > 0


class TestBuildSplitPrompts:
    """测试 build_split_prompts"""

    PARK_ANALYSIS = {
        "theme": "北京环球影城",
        "data_points": "七大主题园区:哈利·波特的魔法世界、变形金刚基地、功夫熊猫盖世之地、侏罗纪世界努布拉岛、小黄人乐园、好莱坞、未来水世界\n游园攻略:建议早9点入园，避开周末",
        "style_description": "活泼明快",
        "color_scheme": ["红色", "金色"],
        "audience": "家庭游客",
        "brand_info": "Universal",
    }

    def test_returns_three_prompts(self):
        prompts = build_split_prompts(self.PARK_ANALYSIS)
        assert len(prompts) == 3

    def test_each_prompt_has_content(self):
        prompts = build_split_prompts(self.PARK_ANALYSIS)
        for p in prompts:
            assert len(p) > 50
            assert "北京环球影城" in p or "七大主题园区" in p or "游园攻略" in p


class TestQualityEvaluation:
    """测试质量评估提示词"""

    def test_build_evaluation_prompt(self):
        prompt = build_quality_evaluation_prompt(
            SAMPLE_REQUIREMENTS, "test prompt", eval_scope="概览"
        )
        assert "AI行业数据报告" in prompt
        assert "test prompt" in prompt
        assert "概览" in prompt

    def test_quality_system_prompt(self):
        assert "内容完整性" in QUALITY_EVALUATION_SYSTEM_PROMPT
        assert "JSON" in QUALITY_EVALUATION_SYSTEM_PROMPT


class TestImprovementPrompt:
    """测试改进提示词"""

    SAMPLE_ANALYSIS = {
        "theme": "测试主题",
        "data_points": "数据点A\n数据点B",
        "style_description": "简约风格",
        "layout_description": "自上而下",
        "color_scheme": ["蓝色"],
    }

    def test_no_issues(self):
        prompt = build_improvement_prompt(self.SAMPLE_ANALYSIS, [], [])
        assert "测试主题" in prompt

    def test_typo_issue(self):
        prompt = build_improvement_prompt(self.SAMPLE_ANALYSIS, ["有错别字"], [])
        assert "100%准确" in prompt

    def test_missing_content(self):
        prompt = build_improvement_prompt(self.SAMPLE_ANALYSIS, ["内容缺失"], [])
        assert "缺失" in prompt or "数据" in prompt


class TestRefinementPrompt:
    """测试需求修改提示词"""

    def test_build_refinement_prompt(self):
        prompt = build_refinement_prompt(SAMPLE_REQUIREMENTS, "把颜色改成蓝色")
        assert "AI行业数据报告" in prompt
        assert "把颜色改成蓝色" in prompt

    def test_refinement_system_prompt(self):
        assert "requirements JSON" in REQUIREMENT_REFINEMENT_SYSTEM_PROMPT
        assert "purpose" in REQUIREMENT_REFINEMENT_SYSTEM_PROMPT