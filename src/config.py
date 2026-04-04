"""
MUSICprompt 统一配置管理
集中管理所有配置项，支持环境变量覆盖和 .env 文件
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, List

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
TOOLS_DIR = PROJECT_ROOT / "tools"


def _load_env_file():
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip("\"'")
                    if key and key not in os.environ:
                        os.environ[key] = value


_load_env_file()


def _env(key: str, default: Any = None, cast: type = str) -> Any:
    value = os.getenv(key, default)
    if value is None:
        return default
    if cast == bool:
        return str(value).lower() in ("1", "true", "yes", "on")
    try:
        return cast(value)
    except (ValueError, TypeError):
        return default


class RedditConfig:
    """Reddit 爬虫配置"""

    SUBREDDITS: List[str] = [
        s.strip() for s in _env(
            "REDDIT_SUBREDDITS",
            "SunoAI,Udio,aiMusic",
        ).split(",")
        if s.strip()
    ]
    MIN_UPVOTES: int = _env("MIN_UPVOTES", 50, int)
    TARGET_COUNT: int = _env("TARGET_COUNT", 7, int)
    RSS_FEED_URL_TEMPLATE: str = (
        "https://www.reddit.com/r/{subreddit}/.rss"
    )
    REQUEST_TIMEOUT: int = _env("REDDIT_REQUEST_TIMEOUT", 30, int)


class PipelineConfig:
    """数据处理流水线配置"""

    MIN_PROMPT_LENGTH: int = _env("MIN_PROMPT_LENGTH", 20, int)
    MAX_PROMPT_LENGTH: int = _env("MAX_PROMPT_LENGTH", 2000, int)
    MIN_QUALITY_SCORE: float = _env("MIN_QUALITY_SCORE", 5.0, float)
    BATCH_SIZE: int = _env("BATCH_SIZE", 20, int)
    RAW_PROMPTS_FILE = DATA_DIR / "raw" / "raw_prompts.txt"


class LLMConfig:
    """LLM 服务配置"""

    SILICONFLOW_API_KEY: Optional[str] = _env(
        "SILICONFLOW_API_KEY"
    )
    GEMINI_API_KEY: Optional[str] = _env("GEMINI_API_KEY")
    SILICONFLOW_BASE_URL: str = _env(
        "SILICONFLOW_BASE_URL",
        "https://api.siliconflow.cn/v1",
    )
    SILICONFLOW_MODEL: str = _env(
        "SILICONFLOW_MODEL",
        "Qwen/Qwen2.5-72B-Instruct",
    )
    GEMINI_MODEL: str = _env(
        "GEMINI_MODEL",
        "gemini-2.5-flash-preview-05-20",
    )
    REQUEST_INTERVAL: float = _env(
        "LLM_REQUEST_INTERVAL", 0.5, float
    )


class DatabaseConfig:
    """数据库配置"""

    DB_PATH: str = _env("DB_PATH", str(DATA_DIR / "musicprompts.db"))
    SEARCH_LIMIT_DEFAULT: int = _env(
        "SEARCH_LIMIT_DEFAULT", 20, int
    )


class OutputConfig:
    """输出配置"""

    FINAL_OUTPUT_DIR = DATA_DIR / "final_output"
    PROMPTS_OUTPUT_DIR = PROJECT_ROOT / "prompts"
    PROCESSED_DIR = DATA_DIR / "processed"
    EXTERNAL_DIR = DATA_DIR / "external"


class GitHubSourceConfig:
    """GitHub 数据源配置"""

    SOURCES = [
        {
            "owner": "AlijeeWrites",
            "repo": "suno-ai-prompts-book-pdf-2026-guide",
            "target_files": ["README.md", "prompts.md", "suno-prompts.md"],
            "description": "Suno AI Prompts Book PDF 2026 Guide",
        },
        {
            "owner": "daveshap",
            "repo": "suno",
            "target_files": ["README.md", "prompts.md", "prompts.txt"],
            "description": "Dave Shapiro's Suno Prompts",
        },
        {
            "owner": "mister-magpie",
            "repo": "aims_prompts",
            "target_files": ["README.md", "prompts.md", "prompts.csv"],
            "description": "AI Music Prompts Collection",
        },
        {
            "owner": "naqashmunir21",
            "repo": "awesome-suno-prompts",
            "target_files": ["README.md", "prompts.md", "suno-prompts.md"],
            "description": "Awesome Suno Prompts",
        },
    ]


config = type("Config", (), {
    "reddit": RedditConfig,
    "pipeline": PipelineConfig,
    "llm": LLMConfig,
    "database": DatabaseConfig,
    "output": OutputConfig,
    "github": GitHubSourceConfig,
    "project_root": PROJECT_ROOT,
    "data_dir": DATA_DIR,
    "tools_dir": TOOLS_DIR,
})()
