"""Infographics Agent 基本使用示例

本示例展示如何以编程方式使用 Infographics Agent。

前置条件：
1. 已配置 .env 文件（含 API Key）
2. 已安装依赖: pip install -e .
"""

import json
import logging
import sys
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(message)s")

# 引入包
from infographics_agent import Config, InfographicAgent, load_config


def create_sample_requirements():
    """创建示例需求文件"""
    requirements = {
        "purpose": "2025年全球AI行业数据概览信息图",
        "audience": "科技公司高管和投资者，对AI行业有一定了解",
        "key_data": (
            "全球AI市场规模2025年达$244B，年增长率36.6%\n"
            "中国AI市场规模2025年达$62B\n"
            "主要应用领域：医疗(28%)、金融(24%)、制造(18%)\n"
            "全球AI企业数量：超过50,000家\n"
            "AI相关岗位需求年增长：40%"
        ),
        "narrative": "自上而下的信息层级，先总览后细分",
        "style": "科技蓝为主色调，简约现代风格，配以数据图表",
        "layout": "竖版，顶部标题，中部数据可视化，底部总结展望",
        "brand": "无",
        "image_paths": [],
        "additional_notes": "数据要准确，图表要清晰，整体风格科技感强",
    }

    filepath = Path("example_requirements.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(requirements, f, ensure_ascii=False, indent=2)
    print(f"✅ 已创建示例需求文件: {filepath}")
    return str(filepath)


def main():
    """主函数"""
    try:
        # 1. 加载配置
        print("=" * 60)
        print("  🎨 Infographics Agent 使用示例")
        print("=" * 60)
        print("\n📋 步骤 1: 加载配置...")
        config = load_config()
        print(f"   ✅ 对话模型: {config.chat.model} @ {config.chat.base_url}")
        print(f"   ✅ 多模态模型: {config.multimodal.model}")
        print(f"   ✅ 生图模型: {config.image.model}")

    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        print("\n💡 请确保已创建 .env 文件并配置了 API Key")
        print("   参考 .env.example 文件")
        return 1

    # 2. 创建示例需求
    print("\n📋 步骤 2: 创建示例需求...")
    req_file = create_sample_requirements()

    # 3. 初始化 Agent
    print("\n📋 步骤 3: 初始化 Agent...")
    agent = InfographicAgent(config)

    try:
        # 4. 预览模式（仅分析，不生成）
        print("\n📋 步骤 4: 运行分析预览...")
        print("   (使用 --preview 模式，仅分析需求，不生成图片)\n")
        result = agent.analyze_only(req_file)
        print(f"\n   ✅ 分析完成，提示词长度: {result.get('prompt_length', 0)} 字符")

        # 5. 完整生成（注释掉，避免意外运行消耗 API 额度）
        # print("\n📋 步骤 5: 完整生成信息图...")
        # result = agent.run(req_file)
        # print(f"   ✅ 生成完成，图片已保存到: {result.get('output_dir')}")

    except Exception as e:
        print(f"❌ 运行失败: {e}")
        return 1
    finally:
        agent.close()

    print("\n" + "=" * 60)
    print("  ✅ 示例运行完成!")
    print("=" * 60)
    print("\n💡 完整生成请运行:")
    print("   python -m infographics_agent -r example_requirements.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())