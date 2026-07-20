"""信息图生成 Agent — 主编排器

工作流:
1. 读取需求 JSON (来自 generate-infographic skill)
2. 调用多模态模型分析图文需求
3. 构建优化的信息图生成提示词
4. 调用信息图生成模型生成图片
5. 下载图片到本地
"""

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from infographics_agent.config import Config, ensure_output_dir
from infographics_agent.client import InfographicsClient
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

logger = logging.getLogger("infographics_agent")


class InfographicAgent:
    """信息图生成 Agent"""

    # 有效信息图尺寸映射表
    VALID_SIZES = {
        (1664, 2496): "1664x2496",  # 2:3
        (2496, 1664): "2496x1664",  # 3:2
        (1760, 2368): "1760x2368",  # 3:4
        (2368, 1760): "2368x1760",  # 4:3
        (1824, 2272): "1824x2272",  # 4:5
        (2272, 1824): "2272x1824",  # 5:4
        (2048, 2048): "2048x2048",  # 1:1
        (2752, 1536): "2752x1536",  # 16:9
        (1536, 2752): "1536x2752",  # 9:16
        (3072, 1376): "3072x1376",  # 21:9
        (1344, 3136): "1344x3136",  # 9:21
        (2560, 720): "2560x720",    # 32:9
        (3072, 864): "3072x864",    # 32:9
    }

    # guidance_scale/style 轮换方案
    _PARAM_CYCLES = [
        {"guidance_scale": 7.0},
        {"guidance_scale": 7.5, "style": "vivid"},
        {"guidance_scale": 6.5, "style": "natural"},
        {"guidance_scale": 8.0},
        {"guidance_scale": 7.0, "style": "vivid"},
        {"guidance_scale": 6.0, "style": "natural"},
        {"guidance_scale": 8.0, "style": "vivid"},
    ]

    def __init__(self, config: Config):
        self.config = config
        self.client = InfographicsClient(config)
        self.output_dir = ensure_output_dir(config)
        self.max_improve_rounds = 10  # 自优化最大轮次

    # ─── 公共接口 ─────────────────────────────────────────────

    def run(self, requirements_file: str) -> Dict[str, Any]:
        """执行完整的信息图生成流程（含自优化循环）

        Args:
            requirements_file: 需求 JSON 文件路径

        Returns:
            生成结果
        """
        logger.info("=" * 60)
        logger.info("  🎨 信息图生成 Agent（含自优化）")
        logger.info("=" * 60)

        # Step 1: 加载需求
        logger.info("\n📋 步骤 1/5: 加载需求...")
        requirements = self._load_requirements(requirements_file)
        logger.info(f"   ✅ 需求加载完成")
        logger.info(f"   📌 主题: {requirements.get('purpose', '未指定')}")

        # Step 2: 多模态分析
        logger.info(f"\n🔍 步骤 2/5: 多模态分析需求...")
        logger.info(f"   模型: {self.config.multimodal.model}")
        analysis = self._analyze_requirements(requirements)
        logger.info(f"   ✅ 分析完成")
        logger.info(f"   📊 分析维度: {len(analysis)} 项")

        # Step 3: 拆分内容为多张子图
        logger.info(f"\n📐 步骤 3/5: 拆分内容为多张独立子图...")
        sub_prompts = build_split_prompts(analysis)
        logger.info(f"   ✅ 拆分为 {len(sub_prompts)} 个子图")
        for i, sp in enumerate(sub_prompts):
            theme = "未命名"
            if "【" in sp and "】" in sp:
                theme = sp.split("【")[1].split("】")[0]
            logger.info(f"     📄 子图{i+1}: {theme} ({len(sp)} 字符)")

        # Step 4-5: 逐张生成 + 自优化循环
        logger.info(f"\n🎨 步骤 4/5: 逐张生成子图（每张最多 {self.max_improve_rounds} 轮自优化）...")
        logger.info(f"   模型: {self.config.image.model}")
        logger.info(f"   尺寸: {self.config.image_size}")

        result = self._generate_multi_image(requirements, sub_prompts, analysis)
        n = len(result.get('local_paths', []))
        logger.info(f"   ✅ 全部生成完成，共 {n} 张子图")

        # 汇总结果
        result["requirements_file"] = requirements_file
        result["output_dir"] = str(self.output_dir)

        self._print_summary(result)
        return result

    def analyze_only(self, requirements_file: str) -> Dict[str, Any]:
        """仅执行分析和提示词构建（预览模式，不生成图片）

        Args:
            requirements_file: 需求 JSON 文件路径

        Returns:
            包含分析和提示词的结果字典
        """
        logger.info("=" * 60)
        logger.info("  🔍 信息图需求分析预览")
        logger.info("=" * 60)

        # Step 1: 加载需求
        logger.info("\n📋 步骤 1/3: 加载需求...")
        requirements = self._load_requirements(requirements_file)
        logger.info(f"   ✅ 主题: {requirements.get('purpose', '未指定')}")

        # Step 2: 多模态分析
        logger.info(f"\n🔍 步骤 2/3: 多模态分析需求...")
        logger.info(f"   模型: {self.config.multimodal.model}")
        analysis = self._analyze_requirements(requirements)
        logger.info(f"   ✅ 分析完成\n")

        # Step 3: 构建生成提示词
        logger.info(f"✏️  步骤 3/3: 构建信息图生成提示词...")
        prompt = build_infographic_prompt(analysis)
        logger.info(f"   ✅ 提示词构建完成")
        logger.info(f"   📝 提示词长度: {len(prompt)} 字符\n")

        # 输出分析结果
        print("─" * 60)
        print("  📊 分析结果")
        print("─" * 60)
        for key, value in analysis.items():
            if key != "raw_analysis":
                display = str(value)
                if len(display) > 200:
                    display = display[:200] + "..."
                print(f"   • {key}: {display}")

        print("\n" + "─" * 60)
        print("  📝 生成提示词")
        print("─" * 60)
        print(prompt)
        print("─" * 60)

        # 输出 JSON 结果供 Claude Code 解析
        result = {
            "status": "preview",
            "requirements_file": requirements_file,
            "analysis": {k: v for k, v in analysis.items() if k != "raw_analysis"},
            "prompt": prompt,
            "prompt_length": len(prompt),
        }

        print("\n---RESULT---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("---END---")

        return result

    def refine_and_preview(self, requirements_file: str, feedback: str) -> Dict[str, Any]:
        """根据用户反馈修改需求，然后重新执行分析预览

        Args:
            requirements_file: 需求 JSON 文件路径
            feedback: 用户的修改意见（自然语言）

        Returns:
            包含更新后分析和提示词的结果字典
        """
        logger.info("=" * 60)
        logger.info("  🔧 根据反馈修改需求")
        logger.info("=" * 60)

        # Step 1: 加载当前需求
        logger.info("\n📋 步骤 1/4: 加载当前需求...")
        requirements = self._load_requirements(requirements_file)
        logger.info(f"   ✅ 当前主题: {requirements.get('purpose', '未指定')}")

        # Step 2: 调用多模态模型修改需求
        logger.info(f"\n💬 步骤 2/4: 分析修改意见...")
        logger.info(f"   反馈: {feedback[:100]}{'...' if len(feedback) > 100 else ''}")
        logger.info(f"   模型: {self.config.multimodal.model}")

        refine_prompt = build_refinement_prompt(requirements, feedback)
        response = self.client.multimodal_analyze(
            text=refine_prompt,
            system_prompt=REQUIREMENT_REFINEMENT_SYSTEM_PROMPT,
        )

        # 解析更新后的需求 JSON
        updated_requirements = self._parse_updated_requirements(response, requirements)
        logger.info(f"   ✅ 需求更新完成")

        # 保存更新后的需求
        path = Path(requirements_file)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(updated_requirements, f, ensure_ascii=False, indent=2)
        logger.info(f"   💾 已保存到: {path.resolve()}")

        # Step 3: 多模态分析
        logger.info(f"\n🔍 步骤 3/4: 重新分析需求...")
        logger.info(f"   模型: {self.config.multimodal.model}")
        analysis = self._analyze_requirements(updated_requirements)
        logger.info(f"   ✅ 分析完成\n")

        # Step 4: 构建生成提示词
        logger.info(f"✏️  步骤 4/4: 构建信息图生成提示词...")
        prompt = build_infographic_prompt(analysis)
        logger.info(f"   ✅ 提示词构建完成")
        logger.info(f"   📝 提示词长度: {len(prompt)} 字符\n")

        # 输出更新后的需求摘要
        print("─" * 60)
        print("  📋 更新后的需求")
        print("─" * 60)
        for key in ["purpose", "audience", "key_data", "narrative", "style", "layout"]:
            if key in updated_requirements and updated_requirements[key]:
                val = str(updated_requirements[key])
                if len(val) > 150:
                    val = val[:150] + "..."
                print(f"   • {key}: {val}")

        # 输出分析结果
        print("\n" + "─" * 60)
        print("  📊 分析结果")
        print("─" * 60)
        for key, value in analysis.items():
            if key != "raw_analysis":
                display = str(value)
                if len(display) > 200:
                    display = display[:200] + "..."
                print(f"   • {key}: {display}")

        print("\n" + "─" * 60)
        print("  📝 生成提示词")
        print("─" * 60)
        print(prompt)
        print("─" * 60)

        # 输出 JSON 结果供 Claude Code 解析
        result = {
            "status": "refined",
            "requirements_file": requirements_file,
            "updated_requirements": {
                k: v for k, v in updated_requirements.items()
                if k != "image_paths"
            },
            "analysis": {k: v for k, v in analysis.items() if k != "raw_analysis"},
            "prompt": prompt,
            "prompt_length": len(prompt),
        }

        print("\n---RESULT---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("---END---")

        return result

    # ─── 内部方法 ─────────────────────────────────────────────

    def _generate_multi_image(
        self, requirements: Dict[str, Any], sub_prompts: List[str], analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """逐张生成子图，每张独立运行自优化循环"""
        all_images = []
        all_local_paths = []
        all_sub_results = []

        for sub_idx, sub_prompt in enumerate(sub_prompts):
            # 提取子图主题名
            theme = "子图"
            if "【" in sub_prompt and "】" in sub_prompt:
                theme = sub_prompt.split("【")[1].split("】")[0]

            logger.info(f"\n  ── 子图 {sub_idx+1}/{len(sub_prompts)}：{theme} ──")

            gen_params: Dict[str, Any] = {}
            score_history: List[int] = []
            best_score = -1
            best_path = ""
            best_images = []
            best_prompt = sub_prompt
            final_status = "max_rounds"
            sub_evals = []

            for iteration in range(1, self.max_improve_rounds + 1):
                logger.info(f"\n  第 {iteration}/{self.max_improve_rounds} 轮生成")

                images = self.client.generate_infographic(
                    prompt=sub_prompt,
                    size=self._resolve_size(requirements.get("output_format", "")),
                    **gen_params,
                )

                if not images:
                    logger.warning(f"    ⚠️ 生成失败，无返回图片")
                    continue

                local_paths = self._download_images(images)
                image_path = str(local_paths[0])
                logger.info(f"    🖼️  → {image_path}")

                # 评估（最后一轮不评估，直接采纳）
                if iteration < self.max_improve_rounds:
                    eval_result = self._evaluate_quality(
                        requirements, sub_prompt, image_path, iteration,
                        eval_scope=theme,
                    )
                    sub_evals.append(eval_result)

                    if eval_result.get("pass", False):
                        score = eval_result.get("score", 7)
                        logger.info(f"\n    ✅ 第 {iteration} 轮通过！(score: {score})")
                        final_status = f"passed_round_{iteration}"
                        eval_result["round"] = iteration
                        best_score = score
                        best_path = image_path
                        best_images = images
                        all_images.extend(images)
                        all_local_paths.extend(local_paths)
                        break
                    else:
                        score = eval_result.get("score", 0)
                        score_history.append(score)
                        logger.info(f"\n    🔄 第 {iteration} 轮未通过 (score: {score})")
                        eval_result["round"] = iteration

                        if score > best_score:
                            best_score = score
                            best_path = image_path
                            best_images = images

                        issues = eval_result.get("issues", [])
                        improvements = eval_result.get("improvements", [])
                        gen_params = self._adjust_gen_params(
                            gen_params, score, issues,
                            iteration=iteration, score_history=score_history,
                        )
                        sub_prompt = build_improvement_prompt(
                            analysis, issues, improvements
                        )
                        if gen_params:
                            logger.info(f"    ⚙️  参数轮换: {gen_params}")
                else:
                    logger.info(f"    📌 已达最大轮次，采纳当前结果")
                    all_images.extend(images)
                    all_local_paths.extend(local_paths)
                    if score_history:
                        final_status = f"max_rounds_best_{max(score_history)}"

            all_sub_results.append({
                "theme": theme,
                "final_status": final_status,
                "best_score": best_score,
                "evaluations": sub_evals,
            })

        return {
            "status": "success",
            "final_status": "multi_image",
            "sub_results": all_sub_results,
            "images_generated": len(all_images),
            "local_paths": [str(p) for p in all_local_paths],
            "api_urls": [img.get("url", "") for img in all_images],
            "prompt_length": sum(len(sp) for sp in sub_prompts),
        }

    def _generate_with_self_improve(
        self, requirements: Dict[str, Any], prompt: str, analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成信息图并自动进行多轮质量优化

        循环：生成 → 评估 → 改进提示词 → 重新生成 → ... → 通过或达最大轮次
        """
        current_prompt = prompt
        gen_params: Dict[str, Any] = {}
        score_history: List[int] = []
        all_images = []
        all_local_paths = []
        all_evaluations = []
        final_status = "max_rounds"

        for iteration in range(1, self.max_improve_rounds + 1):
            logger.info(f"\n  ── 第 {iteration}/{self.max_improve_rounds} 轮生成 ──")

            images = self.client.generate_infographic(
                prompt=current_prompt,
                size=self._resolve_size(requirements.get("output_format", "")),
                **gen_params,
            )
            all_images.extend(images)

            if not images:
                logger.warning(f"  ⚠️ 第 {iteration} 轮生成失败，无返回图片")
                continue

            local_paths = self._download_images(images)
            all_local_paths.extend(local_paths)
            image_path = str(local_paths[0])
            logger.info(f"  🖼️  → {image_path}")

            if iteration < self.max_improve_rounds:
                eval_result = self._evaluate_quality(
                    requirements, current_prompt, image_path, iteration
                )
                all_evaluations.append(eval_result)

                if eval_result.get("pass", False):
                    logger.info(f"\n  ✅ 第 {iteration} 轮评估通过！(score: {eval_result.get('score', 'N/A')})")
                    final_status = f"passed_round_{iteration}"
                    break
                else:
                    score = eval_result.get("score", 0)
                    score_history.append(score)
                    logger.info(f"\n  🔄 第 {iteration} 轮未通过 (score: {score})，改进中...")
                    issues = eval_result.get("issues", [])
                    improvements = eval_result.get("improvements", [])
                    for iss in issues:
                        logger.info(f"     ❓ {iss}")
                    current_prompt = build_improvement_prompt(
                        analysis, issues, improvements
                    )
                    logger.info(f"  📝 提示词已重建 ({len(current_prompt)} 字符)")
                    gen_params = self._adjust_gen_params(
                        gen_params, score, issues,
                        iteration=iteration, score_history=score_history,
                    )
                    if gen_params:
                        logger.info(f"  ⚙️  模型参数已调整: {gen_params}")
            else:
                logger.info(f"  📌 已达最大轮次，采用当前结果")
                final_status = "max_rounds"

        eval_summary = []
        for i, ev in enumerate(all_evaluations):
            eval_summary.append({
                "round": i + 1,
                "score": ev.get("score"),
                "pass": ev.get("pass"),
                "issues": ev.get("issues", []),
            })

        return {
            "status": "success",
            "final_status": final_status,
            "improve_rounds": len(all_evaluations) + 1,
            "evaluations": eval_summary,
            "prompt": current_prompt,
            "prompt_length": len(current_prompt),
            "images_generated": len(all_images),
            "local_paths": [str(p) for p in all_local_paths],
            "api_urls": [img.get("url", "") for img in all_images],
        }

    def _evaluate_quality(
        self,
        requirements: Dict[str, Any],
        prompt: str,
        image_path: str,
        iteration: int,
        eval_scope: str = "",
    ) -> Dict[str, Any]:
        """使用多模态模型评估生成图片的质量"""
        logger.info(f"\n  🔍 第 {iteration} 轮质量评估...")
        logger.info(f"   模型: {self.config.multimodal.model}")
        if eval_scope:
            logger.info(f"   范围: {eval_scope}")

        eval_prompt = build_quality_evaluation_prompt(requirements, prompt, eval_scope)
        try:
            response = self.client.multimodal_analyze(
                text=eval_prompt,
                image_paths=[image_path],
                system_prompt=QUALITY_EVALUATION_SYSTEM_PROMPT,
            )

            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response[start:end])
                result.setdefault("pass", False)
                result.setdefault("score", 0)
                result.setdefault("issues", [])
                result.setdefault("improvements", [])
                result.setdefault("summary", "")
                return result
        except Exception as e:
            logger.warning(f"  ⚠️ 评估解析失败: {e}")

        return {
            "pass": False,
            "score": 0,
            "summary": "评估解析异常，无法判断",
            "issues": ["评估模型返回异常，请重试"],
            "improvements": ["保持当前策略继续生成"],
        }

    def _adjust_gen_params(
        self, current_params: Dict[str, Any], score: int, issues: List[str],
        iteration: int = 1, score_history: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """根据轮次轮换模型生成参数"""
        cycle_idx = (iteration - 1) % len(self._PARAM_CYCLES)
        return dict(self._PARAM_CYCLES[cycle_idx])

    def _parse_updated_requirements(
        self, response: str, original: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析模型返回的更新后需求 JSON"""
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                updated = json.loads(json_str)
                merged = {**original, **updated}
                return merged
        except (json.JSONDecodeError, ValueError):
            pass

        logger.warning("   ⚠️ 未能解析更新后的需求，保留原始需求")
        return original

    def _flatten_to_text(self, value: Any, indent: int = 0) -> str:
        """将嵌套的 dict/list 展平为可读文本字符串"""
        prefix = "  " * indent
        if isinstance(value, dict):
            lines = []
            for k, v in value.items():
                formatted_v = self._flatten_to_text(v, indent + 1)
                if "\n" in formatted_v.strip():
                    lines.append(f"{prefix}{k}:\n{formatted_v}")
                else:
                    lines.append(f"{prefix}{k}: {formatted_v.strip()}")
            return "\n".join(lines)
        elif isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, (dict, list)):
                    parts.append(self._flatten_to_text(item, indent))
                else:
                    parts.append(f"{prefix}- {item}")
            return "\n".join(parts)
        else:
            return str(value)

    def _load_requirements(self, filepath: str) -> Dict[str, Any]:
        """加载需求 JSON 文件"""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"需求文件不存在: {filepath}")

        with open(path, "r", encoding="utf-8") as f:
            requirements = json.load(f)

        required_fields = ["purpose", "audience", "key_data"]
        missing = [f for f in required_fields if f not in requirements or not requirements[f]]
        if missing:
            logger.warning(f"   ⚠️ 需求文件缺少字段: {', '.join(missing)}")

        return requirements

    def _analyze_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """使用多模态模型分析需求"""
        analysis_prompt = build_analysis_prompt(requirements)

        image_paths = requirements.get("image_paths", [])
        if isinstance(image_paths, str):
            image_paths = [image_paths] if image_paths else []

        response = self.client.multimodal_analyze(
            text=analysis_prompt,
            image_paths=image_paths if image_paths else None,
            system_prompt=ANALYSIS_SYSTEM_PROMPT,
        )

        analysis = self._parse_analysis_response(response, requirements)
        return analysis

    def _parse_analysis_response(
        self, response: str, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """解析多模态模型的分析响应"""
        CN_KEY_MAP = {
            "主题与目的": "theme",
            "核心主题": "theme",
            "目的": "purpose",
            "核心信息": "data_points",
            "目标受众": "audience",
            "受众": "audience",
            "视觉风格": "style_description",
            "布局建议": "layout_description",
            "布局": "layout",
            "品牌元素": "brand_info",
            "品牌": "brand",
            "数据可视化": "chart_types",
            "叙事结构": "narrative",
            "配色方案": "color_scheme",
            "颜色方案": "color_scheme",
            "文本内容": "text_content",
            "文字内容": "text_content",
        }

        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                raw = json.loads(json_str)
                normalized = {}
                for k, v in raw.items():
                    en_key = CN_KEY_MAP.get(k, k)
                    normalized[en_key] = v

                for key in ["theme", "data_points", "audience", "narrative",
                            "style_description", "layout_description", "brand_info",
                            "text_content", "color_scheme"]:
                    if key in normalized and not isinstance(normalized[key], str):
                        normalized[key] = self._flatten_to_text(normalized[key])

                if "narrative" not in normalized and "layout_description" in normalized:
                    ld = normalized["layout_description"]
                    if isinstance(ld, dict) and "结构" in ld:
                        normalized["narrative"] = ld["结构"]
                    elif isinstance(ld, str) and "中心" in ld:
                        normalized["narrative"] = "中心发散结构"

                return normalized
        except (json.JSONDecodeError, ValueError):
            pass

        return {
            "theme": requirements.get("purpose", "信息图"),
            "purpose": requirements.get("purpose", ""),
            "audience": requirements.get("audience", "大众"),
            "data_points": requirements.get("key_data", ""),
            "narrative": requirements.get("narrative", "自上而下的信息层级"),
            "style_description": requirements.get("style", "专业简洁"),
            "layout_description": requirements.get("layout", "自上而下的信息层级"),
            "color_scheme": ["品牌色", "中性色"],
            "brand_info": requirements.get("brand", "无"),
            "text_content": requirements.get("key_data", ""),
            "raw_analysis": response,
        }

    def _generate_infographic(
        self, prompt: str, requirements: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成信息图"""
        size = self._resolve_size(requirements.get("output_format", ""))
        return self.client.generate_infographic(prompt=prompt, size=size)

    def _resolve_size(self, output_format: str) -> str:
        """从输出格式描述中解析并映射到有效尺寸"""
        m = re.search(r"(\d+)\s*[xX×]\s*(\d+)", output_format)
        if m:
            w, h = int(m.group(1)), int(m.group(2))
            if (w, h) in self.VALID_SIZES:
                return self.VALID_SIZES[(w, h)]
            ratio = w / h if h > 0 else 1
            best = self.config.image_size
            best_diff = float("inf")
            for (vw, vh), vs in self.VALID_SIZES.items():
                vratio = vw / vh
                diff = abs(ratio - vratio)
                if diff < best_diff:
                    best_diff = diff
                    best = vs
            return best
        return self.config.image_size

    def _download_images(self, images: List[Dict[str, Any]]) -> List[Path]:
        """下载生成的图片"""
        paths = []
        for i, img in enumerate(images):
            url = img.get("url", "")
            if url:
                path = self.client.download_image(url, str(self.output_dir))
                paths.append(path)
                logger.info(f"   📁 图片 {i+1}: {path}")
        return paths

    def _print_summary(self, result: Dict[str, Any]) -> None:
        """打印结果摘要"""
        print("\n" + "=" * 60)
        print("  ✅ 信息图生成完成!")
        print("=" * 60)

        if result.get("final_status") == "multi_image":
            sub_results = result.get("sub_results", [])
            for i, sr in enumerate(sub_results):
                theme = sr.get("theme", f"子图{i+1}")
                best_score = sr.get("best_score", "N/A")
                status = sr.get("final_status", "unknown")
                icon = "✅" if "passed" in status else "🔄"
                print(f"   {icon} 子图{i+1}「{theme}」: 最佳评分 {best_score}")
                for ev in sr.get("evaluations", []):
                    ev_round = ev.get("round", "?")
                    ev_score = ev.get("score", "N/A")
                    mark = "✅" if ev.get("pass") else "🔄"
                    print(f"     {mark} 第 {ev_round} 轮评分: {ev_score}")
        else:
            if "final_status" in result:
                rounds = result.get("improve_rounds", 1)
                status = result.get("final_status", "")
                if "passed" in status:
                    print(f"   🔄 自优化: 第 {rounds} 轮通过")
                else:
                    print(f"   🔄 自优化: {rounds} 轮后采纳（达最大轮次）")
                for ev in result.get("evaluations", []):
                    mark = "✅" if ev.get("pass") else "🔄"
                    print(f"     {mark} 第 {ev['round']} 轮评分: {ev.get('score', 'N/A')}")

        print(f"   📂 输出目录: {result.get('output_dir', 'output')}")
        for i, path in enumerate(result.get("local_paths", [])):
            print(f"   🖼️  图片 {i+1}: {path}")
        print(f"   📝 总提示词长度: {result.get('prompt_length', 0)} 字符")
        print("=" * 60)

    def close(self):
        """清理资源"""
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()