"""CLI 入口 — 信息图生成 Agent 命令行工具"""

import argparse
import json
import logging
import sys
from typing import Any, Dict

from infographics_agent.agent import InfographicAgent
from infographics_agent.config import Config, load_config
from infographics_agent.exceptions import ConfigError


def setup_logging(verbose: bool = False) -> None:
    """配置日志

    Args:
        verbose: 是否输出详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def build_parser() -> argparse.ArgumentParser:
    """构建 CLI 参数解析器

    Returns:
        参数解析器
    """
    parser = argparse.ArgumentParser(
        description="信息图生成 Agent — 基于 AI 多模态模型"
    )
    parser.add_argument(
        "-r", "--requirements",
        default="requirements.json",
        help="需求 JSON 文件路径 (默认: requirements.json)",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="仅测试 API 连通性",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="预览模式：仅执行分析和提示词构建，不生成图片",
    )
    parser.add_argument(
        "--refine",
        action="store_true",
        help="修改模式：根据用户反馈修改需求后重新预览",
    )
    parser.add_argument(
        "--feedback",
        type=str,
        default="",
        help="用户的修改意见（与 --refine 配合使用）",
    )
    parser.add_argument(
        "--env",
        help=".env 文件路径",
    )
    parser.add_argument(
        "--output",
        help="输出目录",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="输出详细日志",
    )
    return parser


def override_config(config: Config, args: argparse.Namespace) -> Config:
    """根据 CLI 参数覆盖配置

    Args:
        config: 原始配置
        args: CLI 参数

    Returns:
        更新后的配置
    """
    if args.output:
        import dataclasses
        config_dict = {
            "chat": config.chat,
            "multimodal": config.multimodal,
            "image": config.image,
            "image_size": config.image_size,
            "num_images": config.num_images,
            "request_timeout": config.request_timeout,
            "max_retries": config.max_retries,
            "output_dir": args.output,
        }
        config = Config(**config_dict)
    return config


def main() -> int:
    """CLI 主入口

    Returns:
        退出码
    """
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    # 加载配置
    try:
        config = load_config(args.env)
        config = override_config(config, args)
    except ConfigError as e:
        print(f"❌ 配置错误: {e}", file=sys.stderr)
        return 1

    # 测试模式
    if args.test:
        from infographics_agent.client import test_connection
        print("🔌 测试 API 连通性...")
        success, msg = test_connection(config, verbose=True)
        return 0 if success else 1

    # 运行生成流程
    agent = InfographicAgent(config)
    try:
        # 预览模式（仅分析，不生成）
        if args.preview:
            result = agent.analyze_only(args.requirements)
            return 0

        # 修改模式（根据反馈修改需求后重新预览）
        if args.refine:
            if not args.feedback:
                print("❌ 请提供 --feedback 参数（修改意见）", file=sys.stderr)
                return 1
            result = agent.refine_and_preview(args.requirements, args.feedback)
            return 0

        # 完整生成模式
        result = agent.run(args.requirements)
        # 输出 JSON 结果供 Claude Code 解析
        print("\n---RESULT---")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("---END---")
        return 0
    except Exception as e:
        print(f"\n❌ 生成失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1
    finally:
        agent.close()


if __name__ == "__main__":
    sys.exit(main())