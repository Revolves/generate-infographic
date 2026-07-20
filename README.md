# generate-infographic

> A Claude Code skill for generating professional infographics through AI-powered multi-round requirement collection, multimodal analysis, and automatic image generation.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-purple)]()

## Overview

`generate-infographic` is a Claude Code slash command skill that guides you through a structured workflow to create professional infographics:

1. **Requirement Collection** — 8 rounds of intelligent Q&A to gather your needs
2. **Data Completion** — Automatic web search to fill in missing data
3. **AI Analysis** — Multimodal model analyzes your requirements and designs the layout
4. **Generation** — AI generates the infographic with automatic quality optimization
5. **Iteration** — Natural language feedback for unlimited revisions

## Features

- 🤖 **Three Independent Models** — Configure chat, multimodal, and image generation models separately from different providers
- 📊 **Multimodal Analysis** — Upload reference images for AI style analysis
- 🔄 **Self-Improvement Loop** — Automatic quality evaluation with multi-round improvements
- ✏️ **Natural Language Refinement** — Modify requirements via simple feedback
- 🌐 **Web Search Integration** — Auto-completes missing data from the web
- 🧩 **Multi-Subgraph Support** — Automatically splits complex content into multiple images

## Quick Start

### Prerequisites

- Claude Code CLI
- Python 3.10+
- An API key for an AI model provider (e.g., SenseNova, OpenAI)

### Installation

```bash
# Clone the repository
git clone https://github.com/Revolves/generate-infographic.git
cd generate-infographic

# Install Python dependencies
pip install -e .
```

### Configuration

Create a `.env` file in the project root:

```ini
# Basic configuration (backward compatible)
SENSENOVA_API_KEY=your_api_key_here

# Or configure each model independently:
# CHAT_API_KEY=sk-xxx
# CHAT_BASE_URL=https://api.openai.com/v1
# CHAT_MODEL=gpt-4o

# MULTIMODAL_API_KEY=sk-xxx
# MULTIMODAL_BASE_URL=https://api.sensenova.cn/v1
# MULTIMODAL_MODEL=sensenova-6.7-flash-lite

# IMAGE_API_KEY=sk-xxx
# IMAGE_BASE_URL=https://api.sensenova.cn/v1
# IMAGE_MODEL=sensenova-u1-fast

IMAGE_SIZE=2752x1536
```

### Usage

```bash
# Start Claude Code in the project directory
claude

# Run the skill
/generate-infographic
```

The skill will guide you through the entire process with interactive Q&A.

## Three-Model Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   generate-infographic                   │
├─────────────┬───────────────────┬───────────────────────┤
│  Chat Model  │  Multimodal Model │  Image Gen Model      │
│  (Analysis)  │  (Vision/QA)     │  (Rendering)          │
│             │                   │                       │
│  GPT-4o     │  SenseNova 6.7    │  SenseNova U1 Fast    │
│  Claude     │  GPT-4V           │  DALL-E 3             │
│  etc.       │  Claude Vision    │  Stable Diffusion     │
└─────────────┴───────────────────┴───────────────────────┘
```

Each model can be configured independently with its own endpoint URL, API key, and model name. This allows you to use different providers for different tasks.

### Environment Variables

| Variable | Purpose | Fallback | Default |
|----------|---------|----------|---------|
| `CHAT_API_KEY` | Chat model API Key | → `SENSENOVA_API_KEY` | — |
| `CHAT_BASE_URL` | Chat model endpoint | → `SENSENOVA_BASE_URL` | `https://token.sensenova.cn/v1` |
| `CHAT_MODEL` | Chat model name | — | `sensenova-6.7-flash-lite` |
| `MULTIMODAL_API_KEY` | Multimodal API Key | → `CHAT_API_KEY` | — |
| `MULTIMODAL_BASE_URL` | Multimodal endpoint | → `CHAT_BASE_URL` | — |
| `MULTIMODAL_MODEL` | Multimodal model name | → `CHAT_MODEL` | `sensenova-6.7-flash-lite` |
| `IMAGE_API_KEY` | Image gen API Key | → `MULTIMODAL_API_KEY` | — |
| `IMAGE_BASE_URL` | Image gen endpoint | → `MULTIMODAL_BASE_URL` | — |
| `IMAGE_MODEL` | Image gen model name | — | `sensenova-u1-fast` |
| `IMAGE_SIZE` | Default image size | — | `2752x1536` |
| `REQUEST_TIMEOUT` | Request timeout (s) | — | `120` |
| `MAX_RETRIES` | Max retry count | — | `3` |
| `OUTPUT_DIR` | Output directory | — | `output` |

## Skill Workflow

### Phase 1: Requirement Collection (8 Rounds)

| Round | Topic | Record Field |
|-------|-------|-------------|
| 1 | Topic & Purpose | `purpose` |
| 2 | Target Audience | `audience` |
| 3 | Key Data & Content | `key_data` |
| 4 | Narrative Structure | `narrative` |
| 5 | Visual Style & Colors | `style` |
| 6 | Layout & Size | `layout` |
| 7 | Brand Elements | `brand` |
| 8 | Additional Notes | `additional_notes` |

### Phase 2: Web Search Data Completion

The skill automatically detects missing data and uses WebSearch to fill in gaps, then asks for your confirmation.

### Phase 3: Preview, Confirm & Generate

1. **Preview** — AI analyzes your requirements and builds a generation prompt
2. **Confirm** — Review the prompt and confirm, or provide natural language feedback
3. **Generate** — Infographic is generated with automatic quality optimization (up to 10 rounds)
4. **Iterate** — Unlimited revision cycle: feedback → refine → preview → confirm

## Project Structure

```
generate-infographic/
├── .claude/
│   ├── skills/
│   │   └── generate-infographic.md  # Skill definition (bilingual)
│   └── settings.local.json          # Skill registration
├── infographics_agent/             # Python package
│   ├── __init__.py
│   ├── cli.py                      # CLI entry point
│   ├── config.py                   # Three-model configuration
│   ├── client.py                   # Multi-provider API client
│   ├── agent.py                    # Main orchestrator
│   ├── exceptions.py               # Custom exceptions
│   └── prompt_templates.py         # Prompt templates
├── src/                            # Backward compatibility shims
├── tests/                          # Test suite
├── docs/                           # Documentation
├── examples/                       # Usage examples
├── CLAUDE.md                       # Claude Code project instructions
├── pyproject.toml                  # Build configuration
├── LICENSE                         # MIT License
└── README.md                       # This file
```

## CLI Commands

```bash
# Test API connectivity
python -m infographics_agent --test

# Analyze requirements and preview the prompt
python -m infographics_agent --preview -r requirements.json

# Full generation
python -m infographics_agent -r requirements.json

# Modify requirements and re-preview
python -m infographics_agent --refine --feedback "Change colors to blue" -r requirements.json
```

## Requirements File Format

The `requirements.json` file generated by the skill:

```json
{
  "purpose": "Infographic topic and purpose",
  "audience": "Target audience description",
  "key_data": "Key data and content to display",
  "narrative": "Narrative structure preference",
  "style": "Visual style and color preference",
  "layout": "Layout and size requirements",
  "brand": "Brand information",
  "image_paths": ["Reference image paths (optional)"],
  "additional_notes": "Additional notes (optional)"
}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Code formatting
black infographics_agent/
ruff check infographics_agent/
```

## License

[MIT License](LICENSE) © 2026