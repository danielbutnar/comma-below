"""Every model Kaggle Benchmarks served in October 2026, with the facts the analysis groups by.

`line` groups versions of one product line; `version` orders them (higher = newer). Sizes and
release dates are not used: the labs do not publish them for most of these models.
"""

from __future__ import annotations

# slug: (display name, lab, line, version, open weights, reasoning)
MODELS = {
    "claude-opus-4-5-20251101": ("Claude Opus 4.5", "Anthropic", "Claude Opus", 4.5, False, None),
    "claude-opus-4-6-default": ("Claude Opus 4.6", "Anthropic", "Claude Opus", 4.6, False, None),
    "claude-opus-4-7-default": ("Claude Opus 4.7", "Anthropic", "Claude Opus", 4.7, False, None),
    "claude-opus-4-8-default": ("Claude Opus 4.8", "Anthropic", "Claude Opus", 4.8, False, None),
    "claude-opus-5-default": ("Claude Opus 5", "Anthropic", "Claude Opus", 5.0, False, None),
    "claude-opus-5-5-default": ("Claude Opus 5.5", "Anthropic", "Claude Opus", 5.5, False, None),
    "claude-sonnet-4-5-20250929": ("Claude Sonnet 4.5", "Anthropic", "Claude Sonnet", 4.5, False, None),
    "claude-sonnet-4-6-default": ("Claude Sonnet 4.6", "Anthropic", "Claude Sonnet", 4.6, False, None),
    "claude-sonnet-5-default": ("Claude Sonnet 5", "Anthropic", "Claude Sonnet", 5.0, False, None),
    "claude-sonnet-5-5-default": ("Claude Sonnet 5.5", "Anthropic", "Claude Sonnet", 5.5, False, None),
    "claude-haiku-4-5-20251001": ("Claude Haiku 4.5", "Anthropic", "Claude Haiku", 4.5, False, None),
    "claude-haiku-5-5": ("Claude Haiku 5.5", "Anthropic", "Claude Haiku", 5.5, False, None),
    "gemini-2.5-flash": ("Gemini 2.5 Flash", "Google", "Gemini Flash", 2.5, False, None),
    "gemini-3-flash-preview": ("Gemini 3 Flash", "Google", "Gemini Flash", 3.0, False, None),
    "gemini-3.5-flash": ("Gemini 3.5 Flash", "Google", "Gemini Flash", 3.5, False, None),
    "gemini-3.6-flash": ("Gemini 3.6 Flash", "Google", "Gemini Flash", 3.6, False, None),
    "gemini-3.7-flash": ("Gemini 3.7 Flash", "Google", "Gemini Flash", 3.7, False, None),
    "gemini-3.8-flash": ("Gemini 3.8 Flash", "Google", "Gemini Flash", 3.8, False, None),
    "gemini-2.5-pro": ("Gemini 2.5 Pro", "Google", "Gemini Pro", 2.5, False, None),
    "gemini-3.1-pro-preview": ("Gemini 3.1 Pro", "Google", "Gemini Pro", 3.1, False, None),
    "gemini-3.1-flash-lite-preview": ("Gemini 3.1 Flash-Lite", "Google", "Gemini Flash-Lite", 3.1, False, None),
    "gemini-3.5-flash-lite": ("Gemini 3.5 Flash-Lite", "Google", "Gemini Flash-Lite", 3.5, False, None),
    "gemma-4-26b-a4b-it": ("Gemma 4 26B A4B", "Google", "Gemma 4", 4.0, True, None),
    "gemma-4-31b-it": ("Gemma 4 31B", "Google", "Gemma 4", 4.1, True, None),
    "gpt-5.4-nano-2026-03-17": ("GPT-5.4 nano", "OpenAI", "GPT small", 5.4, False, None),
    "gpt-5.4-mini-2026-03-17": ("GPT-5.4 mini", "OpenAI", "GPT small", 5.41, False, None),
    "gpt-5.4-2026-03-05": ("GPT-5.4", "OpenAI", "GPT", 5.4, False, None),
    "gpt-5.5-2026-04-23": ("GPT-5.5", "OpenAI", "GPT", 5.5, False, None),
    "gpt-5.6-luna": ("GPT-5.6 Luna", "OpenAI", "GPT Luna", 5.6, False, None),
    "gpt-6-luna": ("GPT-6 Luna", "OpenAI", "GPT Luna", 6.0, False, None),
    "gpt-5.6-terra": ("GPT-5.6 Terra", "OpenAI", "GPT Terra", 5.6, False, None),
    "gpt-5.6-sol": ("GPT-5.6 Sol", "OpenAI", "GPT Sol", 5.6, False, None),
    "gpt-6-sol": ("GPT-6 Sol", "OpenAI", "GPT Sol", 6.0, False, None),
    "gpt-6.1-sol": ("GPT-6.1 Sol", "OpenAI", "GPT Sol", 6.1, False, None),
    "gpt-6-astra": ("GPT-6 Astra", "OpenAI", "GPT Astra", 6.0, False, None),
    "gpt-oss-20b": ("gpt-oss-20b", "OpenAI", "gpt-oss", 1.0, True, None),
    "gpt-oss-120b": ("gpt-oss-120b", "OpenAI", "gpt-oss", 1.1, True, None),
    "grok-4.20-0309-reasoning": ("Grok 4.20 Reasoning", "xAI", "Grok 4.20", 4.2, False, True),
    "grok-4.20-0309-non-reasoning": ("Grok 4.20 Non-Reasoning", "xAI", "Grok 4.20", 4.2, False, False),
    "grok-4.5-0708": ("Grok 4.5", "xAI", "Grok", 4.5, False, None),
    "grok-4.6": ("Grok 4.6", "xAI", "Grok", 4.6, False, None),
    "deepseek-r1-0528": ("DeepSeek-R1", "DeepSeek", "DeepSeek-R1", 1.0, True, True),
    "qwen3-235b-a22b-instruct-2507": ("Qwen 3 235B", "Alibaba", "Qwen 3", 3.0, True, False),
    "qwen3-coder-480b-a35b-instruct": ("Qwen 3 Coder 480B", "Alibaba", "Qwen 3 Coder", 3.0, True, False),
    "qwen3-next-80b-a3b-instruct": ("Qwen 3 Next 80B Instruct", "Alibaba", "Qwen 3 Next", 3.1, True, False),
    "qwen3-next-80b-a3b-thinking": ("Qwen 3 Next 80B Thinking", "Alibaba", "Qwen 3 Next", 3.1, True, True),
    "glm-5": ("GLM-5", "Zhipu", "GLM", 5.0, True, None),
}

# The 15 models of Round 1 (tasks 1-7).
CORE = [
    "claude-opus-5-default", "claude-sonnet-5-default", "claude-haiku-4-5-20251001",
    "gemini-3.1-pro-preview", "gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite", "gemma-4-31b-it",
    "gpt-6-astra", "gpt-5.5-2026-04-23", "gpt-5.4-nano-2026-03-17",
    "grok-4.20-0309-reasoning", "deepseek-r1-0528", "qwen3-235b-a22b-instruct-2507", "glm-5",
]

# Product lines whose members are successive versions (other lines group sizes or modes).
VERSION_LINES = {"Claude Opus", "Claude Sonnet", "Claude Haiku", "Gemini Flash", "Gemini Pro", "Gemini Flash-Lite",
                 "GPT", "GPT Sol", "GPT Luna"}

# Same model with reasoning on and off.
REASONING_PAIRS = [
    ("grok-4.20-0309-reasoning", "grok-4.20-0309-non-reasoning"),
    ("qwen3-next-80b-a3b-thinking", "qwen3-next-80b-a3b-instruct"),
]


def name(slug: str) -> str:
    return MODELS.get(slug, (slug,))[0]


def lab(slug: str) -> str:
    return MODELS.get(slug, (None, "?"))[1]


def line(slug: str) -> str:
    return MODELS.get(slug, (None, None, "?"))[2]


def version(slug: str) -> float:
    return MODELS.get(slug, (None, None, None, 0.0))[3]


def open_weights(slug: str) -> bool:
    return bool(MODELS.get(slug, (None, None, None, None, False))[4])
