# MUSICprompt 自动化流水线项目架构�?
## 文档信息

| 项目名称 | MUSICprompt 海外音频情报中转�?|
|---------|------------------------|
| 文档版本 | v1.0.1 |
| 编写日期 | 2026-03-23 |
| 文档状�?| 已批�?|
| 密级 | 内部公开 |

---

## 目录

1. [项目概述](#1-项目概述)
2. [系统架构](#2-系统架构)
3. [技术选型](#3-技术选型)
4. [模块详细设计](#4-模块详细设计)
5. [数据流程与协议](#5-数据流程与协�?
6. [部署架构](#6-部署架构)
7. [风险评估与应对策略](#7-风险评估与应对策�?
8. [系统局限性分析](#8-系统局限性分�?
9. [未来拓展规划](#9-未来拓展规划)
10. [附录](#10-附录)

---

## 1. 项目概述

### 1.1 项目背景

随着 AI 音乐生成工具（Suno、Udio 等）的普及，海外社区涌现大量优质 Prompt 资源。国内创作者面临以下痛点：

- **语言壁垒**：优�?Prompt 多为英文，国内用户理解成本高
- **信息分散**：高质量内容散落�?Reddit 等多个平台，检索困�?- **缺乏标准�?*：Prompt 缺乏统一的参数化描述，难以复用和优化
- **时效性差**：热门趋势传播滞后，错过最佳创作窗口期

### 1.2 项目定位

本项目定位为 **"海外音频情报中转�?**，而非简单的内容搬运平台。核心价值在于：

```
原始情报 �?智能炼金 �?协议标准�?�?本地化输�?�?价值增�?```

### 1.3 项目目标

| 目标类型 | 具体指标 |
|---------|---------|
| 数据采集 | 每日自动抓取 r/SunoAI、r/Udio 等社�?Top 内容 |
| 智能处理 | 自动翻译、参数填充、标签生�?|
| 标准输出 | 生成符合 MUSICprompt 协议�?JSON 数据 |
| 自动部署 | 全流程自动化，零人工干预 |
| 用户价�?| 提供可直接使用的 Prompt 及专业优化建�?|

### 1.4 核心价值主�?
1. **双语对照**：中英文 Prompt 并列展示，降低理解门�?2. **DSP 参数增强**：AI 自动补充专业音频参数建议
3. **本土化标�?*：抖音热门标签对齐，便于内容创作者使�?4. **可追溯�?*：保留原始来源链接，确保数据可信�?
---

## 2. 系统架构

### 2.1 整体架构�?
```
┌─────────────────────────────────────────────────────────────────────────────�?�?                       MUSICprompt 自动化流水线架构                                  �?├─────────────────────────────────────────────────────────────────────────────�?�?                                                                            �?�? ┌──────────────�?   ┌──────────────�?   ┌──────────────�?   ┌───────────�?�?�? �?  Phase 1    �?   �?  Phase 2    �?   �?  Phase 3    �?   �? Phase 4  �?�?�? �?  采集阶段    │───▶│  炼金阶段    │───▶│  视觉阶段    │───▶│  部署阶段 �?�?�? �? (Scraping)  �?   �?(Alchemist)  �?   �? (Herald)    �?   �? (CI/CD)  �?�?�? └──────────────�?   └──────────────�?   └──────────────�?   └───────────�?�?�?        �?                  �?                  �?                  �?      �?�?        �?                  �?                  �?                  �?      �?�? ┌──────────────�?   ┌──────────────�?   ┌──────────────�?   ┌───────────�?�?�? �?Reddit API   �?   �?Gemini 2.0   �?   �?Jinja2 +     �?   �?GitHub    �?�?�? �?PRAW/Requests�?   �?Flash API    �?   �?Pillow       �?   �?Actions   �?�?�? └──────────────�?   └──────────────�?   └──────────────�?   └───────────�?�?�?                                                                            �?└─────────────────────────────────────────────────────────────────────────────�?```

### 2.2 四阶段流水线详解

#### 2.2.1 Phase 1: 采集阶段 (Scraping)

```
┌─────────────────────────────────────────────────────────────�?�?                    采集模块架构                             �?├─────────────────────────────────────────────────────────────�?�?                                                            �?�?  ┌─────────────�?     ┌─────────────�?     ┌───────────�? �?�?  �? Reddit API �?     �? 过滤引擎   �?     �? 去重存储 �? �?�?  �? Connector  │─────▶│  Filter     │─────▶│  Dedup    �? �?�?  └─────────────�?     └─────────────�?     └───────────�? �?�?        �?                    �?                   �?       �?�?        �?                    �?                   �?       �?�?  ┌─────────────�?     ┌─────────────�?     ┌───────────�? �?�?  �?r/SunoAI    �?     �?Upvote �?N  �?     �?raw_data/ �? �?�?  �?r/Udio      �?     �?Has Prompt  �?     �? .json    �? �?�?  �?r/aiMusic   �?     �?Has Tags    �?     �?          �? �?�?  └─────────────�?     └─────────────�?     └───────────�? �?�?                                                            �?└─────────────────────────────────────────────────────────────�?```

**采集策略**�?
| 参数 | 配置�?| 说明 |
|-----|-------|------|
| 采集频率 | 每日 1 �?| 通过 GitHub Actions 定时触发 |
| 时间窗口 | 过去 24 小时 | 确保内容新鲜�?|
| 排序依据 | Upvote 降序 | 优先采集高热度内�?|
| 最小票�?| 可配置（默认 50�?| 过滤低质量内�?|
| 内容过滤 | 必须包含 Prompt 文本 | 确保内容可用�?|

#### 2.2.2 Phase 2: 协议化炼金阶�?(Alchemist Agent)

```
┌─────────────────────────────────────────────────────────────�?�?                   炼金模块架构                              �?├─────────────────────────────────────────────────────────────�?�?                                                            �?�?  ┌─────────────────────────────────────────────────────�? �?�?  �?                 Gemini 2.0 Flash                    �? �?�?  �?                   Processing Core                   �? �?�?  └─────────────────────────────────────────────────────�? �?�?                           �?                               �?�?        ┌──────────────────┼──────────────────�?           �?�?        �?                 �?                 �?           �?�?  ┌───────────�?    ┌───────────�?     ┌───────────�?     �?�?  �?翻译引擎  �?    �?参数填充  �?     �?标签生成  �?     �?�?  �?Translate �?    �?DSP Fill  �?     �?Tag Gen   �?     �?�?  └───────────�?    └───────────�?     └───────────�?     �?�?        �?                 �?                 �?           �?�?        �?                 �?                 �?           �?�?  ┌───────────�?    ┌───────────�?     ┌───────────�?     �?�?  �?中英双语  �?    �?BPM       �?     �?抖音标签  �?     �?�?  �?对照输出  �?    �?Energy    �?     �?#治愈     �?     �?�?  �?          �?    �?Frequency �?     �?#爆改     �?     �?�?  �?          �?    �?Key       �?     �?#氛围�?  �?     �?�?  └───────────�?    └───────────�?     └───────────�?     �?�?                                                            �?└─────────────────────────────────────────────────────────────�?```

**处理逻辑详解**�?
```python
# 伪代码示�?class AlchemistAgent:
    def process(self, raw_content: RawContent) -> MUSICpromptDocument:
        # Step 1: 双语翻译
        bilingual = self.translate_to_bilingual(raw_content.text)
        
        # Step 2: DSP 参数推断
        dsp_params = self.infer_dsp_parameters(
            genre=raw_content.tags,
            mood=raw_content.description
        )
        
        # Step 3: 抖音标签对齐
        douyin_tags = self.align_douyin_tags(
            content_type=raw_content.type,
            trending_topics=self.get_trending_topics()
        )
        
        # Step 4: 专业建议生成
        gem_suggestion = self.generate_professional_suggestion(dsp_params)
        
        return MUSICpromptDocument(
            original=raw_content,
            bilingual=bilingual,
            dsp_params=dsp_params,
            douyin_tags=douyin_tags,
            gem_suggestion=gem_suggestion
        )
```

#### 2.2.3 Phase 3: 视觉与文档阶�?(The Herald)

```
┌─────────────────────────────────────────────────────────────�?�?                   视觉模块架构                              �?├─────────────────────────────────────────────────────────────�?�?                                                            �?�?  ┌─────────────�?     ┌─────────────�?     ┌───────────�? �?�?  �?JSON 更新   �?     �?文档渲染    �?     �?图片生成  �? �?�?  �?DB Update   │─────▶│ Doc Render  │─────▶│ Img Gen   �? �?�?  └─────────────�?     └─────────────�?     └───────────�? �?�?        �?                    �?                   �?       �?�?        �?                    �?                   �?       �?�?  ┌─────────────�?     ┌─────────────�?     ┌───────────�? �?�?  �?MUSICprompt_db.json�?     �?README.md   �?     �?爆款指数图│  �?�?  �?            �?     �?双语表格    �?     �?社交分享图│  �?�?  �?            �?     �?分类索引    �?     �?          �? �?�?  └─────────────�?     └─────────────�?     └───────────�? �?�?                                                            �?└─────────────────────────────────────────────────────────────�?```

**输出产物**�?
| 产物类型 | 文件�?| 用�?|
|---------|-------|------|
| 结构化数�?| `MUSICprompt_db.json` | 机器可读的完整数据库 |
| 文档页面 | `README.md` | GitHub 仓库主页展示 |
| 分类索引 | `docs/categories/*.md` | 按风格分类的 Prompt 列表 |
| 社交图片 | `assets/cards/*.png` | 小红�?朋友圈分享素�?|

#### 2.2.4 Phase 4: 自动部署阶段 (CI/CD)

```
┌─────────────────────────────────────────────────────────────�?�?                   CI/CD 流程架构                            �?├─────────────────────────────────────────────────────────────�?�?                                                            �?�?  ┌─────────────�?     ┌─────────────�?     ┌───────────�? �?�?  �?定时触发    �?     �?流水线执�? �?     �?自动提交  �? �?�?  �?Cron Trigger│─────▶│ Pipeline    │─────▶│ Git Push  �? �?�?  └─────────────�?     └─────────────�?     └───────────�? �?�?        �?                    �?                   �?       �?�?        �?                    �?                   �?       �?�?  ┌─────────────�?     ┌─────────────�?     ┌───────────�? �?�?  �?UTC 00:00   �?     �?Phase 1-3   �?     �?main分支  �? �?�?  �?(北京时间   �?     �?顺序执行    �?     �?自动更新  �? �?�?  �? 08:00)     �?     �?            �?     �?          �? �?�?  └─────────────�?     └─────────────�?     └───────────�? �?�?                                                            �?└─────────────────────────────────────────────────────────────�?```

---

## 3. 技术选型

### 3.1 技术栈总览

```
┌─────────────────────────────────────────────────────────────�?�?                     技术栈全景�?                           �?├─────────────────────────────────────────────────────────────�?�?                                                            �?�? ┌─────────────────────────────────────────────────────�?  �?�? �?                   基础设施�?                       �?  �?�? �? GitHub Actions (免费 Runner) + GitHub Repository    �?  �?�? └─────────────────────────────────────────────────────�?  �?�?                           �?                               �?�? ┌─────────────────────────────────────────────────────�?  �?�? �?                   AI 能力�?                        �?  �?�? �? Google Gemini 2.0 Flash API (免费额度)              �?  �?�? └─────────────────────────────────────────────────────�?  �?�?                           �?                               �?�? ┌─────────────────────────────────────────────────────�?  �?�? �?                   核心应用�?                       �?  �?�? �? Python 3.11+ | PRAW | Requests | Jinja2 | Pillow   �?  �?�? └─────────────────────────────────────────────────────�?  �?�?                           �?                               �?�? ┌─────────────────────────────────────────────────────�?  �?�? �?                   数据存储�?                       �?  �?�? �? JSON Files | Markdown | Git Version Control        �?  �?�? └─────────────────────────────────────────────────────�?  �?�?                                                            �?└─────────────────────────────────────────────────────────────�?```

### 3.2 详细技术选型�?
| 层级 | 组件 | 选型方案 | 选型理由 |
|-----|------|---------|---------|
| **基础设施** | CI/CD 平台 | GitHub Actions | 免费、与仓库原生集成、支持定时任�?|
| | 代码托管 | GitHub Repository | 公开免费、社区友好、便于传�?|
| **AI 能力** | LLM 服务 | Gemini 2.0 Flash | 免费额度高、响应快、多语言支持�?|
| **数据采集** | Reddit API | PRAW (Python Reddit API Wrapper) | 官方推荐、功能完整、社区活�?|
| | HTTP 客户�?| Requests | 简单易用、功能完�?|
| **数据处理** | 编程语言 | Python 3.11+ | 生态丰富、AI 集成友好 |
| | 模板引擎 | Jinja2 | 灵活强大、支持复杂模�?|
| | 图像处理 | Pillow (PIL) | Python 标准图像库、功能全�?|
| **数据存储** | 数据格式 | JSON | 机器可读、易于解析、Git 友好 |
| | 文档格式 | Markdown | GitHub 原生支持、渲染美�?|
| **版本控制** | VCS | Git | 行业标准、分支管理强�?|

### 3.3 依赖清单

```toml
# pyproject.toml
[project]
name = "MUSICprompt-pipeline"
version = "1.0.0"
requires-python = ">=3.11"

dependencies = [
    "praw>=7.7.0",           # Reddit API 客户�?    "requests>=2.31.0",      # HTTP 请求
    "google-generativeai>=0.3.0",  # Gemini API
    "jinja2>=3.1.0",         # 模板引擎
    "pillow>=10.0.0",        # 图像处理
    "pydantic>=2.0.0",       # 数据验证
    "python-dotenv>=1.0.0",  # 环境变量管理
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]
```

---

## 4. 模块详细设计

### 4.1 项目目录结构

```
MUSICprompt-pipeline/
├── .github/
�?  └── workflows/
�?      └── daily-pipeline.yml     # GitHub Actions 工作�?├── src/
�?  ├── __init__.py
�?  ├── __main__.py                # 主入口脚�?�?  ├── scraper/                   # Phase 1: 采集模块
�?  �?  ├── __init__.py
�?  �?  ├── __main__.py            # 采集模块入口
�?  �?  ├── reddit_client.py       # Reddit API 封装
�?  �?  ├── filters.py             # 内容过滤�?�?  �?  └── dedup.py               # 去重逻辑
�?  ├── alchemist/                 # Phase 2: 炼金模块
�?  �?  ├── __init__.py
�?  �?  ├── __main__.py            # 炼金模块入口
�?  �?  ├── gemini_client.py       # Gemini API 封装
�?  �?  ├── translator.py          # 翻译引擎
�?  �?  ├── dsp_inferencer.py      # DSP 参数推断
�?  �?  └── tag_generator.py       # 标签生成�?�?  ├── herald/                    # Phase 3: 视觉模块
�?  �?  ├── __init__.py
�?  �?  ├── __main__.py            # 视觉模块入口
�?  �?  ├── db_manager.py          # 数据库管�?�?  �?  ├── doc_renderer.py        # 文档渲染�?�?  �?  └── image_generator.py     # 图片生成�?�?  ├── models/                    # 数据模型
�?  �?  ├── __init__.py
�?  �?  ├── raw_content.py         # 原始内容模型
�?  �?  └── MUSICprompt_document.py       # MUSICprompt 文档模型
�?  └── utils/                     # 工具函数
�?      ├── __init__.py
�?      ├── rate_limiter.py        # 速率限制
�?      └── logger.py              # 日志工具
├── templates/                     # Jinja2 模板
�?  ├── readme.md.j2               # README 模板（含免责声明�?�?  └── category.md.j2             # 分类页模�?├── assets/                        # 静态资�?�?  ├── cards/                     # 生成的社交图�?�?  └── backgrounds/               # 图片背景素材
├── data/                          # 数据文件
�?  ├── MUSICprompt_db.json               # 主数据库
�?  └── raw/                       # 原始采集数据
├── docs/                          # 文档目录
�?  └── categories/                # 分类文档
├── tests/                         # 测试目录
�?  ├── test_scraper.py
�?  ├── test_alchemist.py
�?  └── test_herald.py
├── .env.example                   # 环境变量示例
├── pyproject.toml                 # 项目配置
├── README.md                      # 项目说明
└── ARCHITECTURE.md                # 本架构文�?```

### 4.2 核心类设�?
#### 4.2.1 数据模型

```python
# src/models/raw_content.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


class RawContent(BaseModel):
    """原始采集内容模型"""
    id: str = Field(..., description="Reddit 帖子 ID")
    title: str = Field(..., description="帖子标题")
    author: str = Field(..., description="作者用户名")
    subreddit: str = Field(..., description="来源子版�?)
    upvotes: int = Field(..., description="点赞�?)
    prompt_text: Optional[str] = Field(None, description="Prompt 文本")
    tags: List[str] = Field(default_factory=list, description="风格标签")
    url: str = Field(..., description="原帖链接")
    created_at: datetime = Field(..., description="发布时间")
    collected_at: datetime = Field(default_factory=datetime.now, description="采集时间")


# src/models/MUSICprompt_document.py
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class EnergyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class DSPParameters(BaseModel):
    """DSP 参数模型"""
    bpm: Optional[int] = Field(None, ge=40, le=220, description="节拍速度")
    key: Optional[str] = Field(None, description="调性，�?C Major, A Minor")
    energy_level: EnergyLevel = Field(EnergyLevel.MEDIUM, description="能量等级")
    frequency_center: Optional[str] = Field(None, description="频率中心")
    dynamics_range: Optional[str] = Field(None, description="动态范�?)


class BilingualText(BaseModel):
    """双语文本模型"""
    en: str = Field(..., description="英文原文")
    zh: str = Field(..., description="中文翻译")


class MUSICpromptDocument(BaseModel):
    """MUSICprompt 标准文档模型"""
    id: str = Field(..., description="文档唯一标识")
    version: str = Field("1.0.0", description="MUSICprompt 协议版本")
    source: RawContent = Field(..., description="原始来源")
    title: BilingualText = Field(..., description="双语标题")
    prompt: BilingualText = Field(..., description="双语 Prompt")
    tags: List[str] = Field(default_factory=list, description="原始标签")
    douyin_tags: List[str] = Field(default_factory=list, description="抖音标签")
    dsp_params: DSPParameters = Field(..., description="DSP 参数")
    gem_suggestion: str = Field(..., description="Gem 专业建议")
    viral_score: float = Field(..., ge=0, le=100, description="爆款指数")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

#### 4.2.2 采集模块

```python
# src/scraper/reddit_client.py
import praw
from typing import List, Optional
from datetime import datetime, timedelta
import os

from models.raw_content import RawContent
from .filters import ContentFilter
from .dedup import Deduplicator


class RedditScraper:
    """Reddit 内容采集�?""
    
    TARGET_SUBREDDITS = ["SunoAI", "Udio", "aiMusic"]
    TIME_WINDOW_HOURS = 24
    MIN_UPVOTES = 50
    
    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=os.getenv("REDDIT_CLIENT_ID"),
            client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
            user_agent="MUSICprompt-Pipeline/1.0"
        )
        self.filter = ContentFilter()
        self.dedup = Deduplicator()
    
    def fetch_top_posts(self, subreddit: str, limit: int = 100) -> List[RawContent]:
        """获取指定子版块的热门帖子"""
        sub = self.reddit.subreddit(subreddit)
        time_filter = "day"  # 过去 24 小时
        
        posts = []
        for post in sub.top(time_filter=time_filter, limit=limit):
            if self._should_include(post):
                content = self._convert_to_model(post)
                if not self.dedup.is_duplicate(content):
                    posts.append(content)
                    self.dedup.mark_processed(content)
        
        return posts
    
    def _should_include(self, post) -> bool:
        """判断帖子是否符合采集条件"""
        return (
            post.score >= self.MIN_UPVOTES
            and self.filter.has_prompt(post)
            and self.filter.has_tags(post)
            and not post.over_18
        )
    
    def _convert_to_model(self, post) -> RawContent:
        """�?Reddit 帖子转换为数据模�?""
        return RawContent(
            id=post.id,
            title=post.title,
            author=str(post.author),
            subreddit=post.subreddit.display_name,
            upvotes=post.score,
            prompt_text=self.filter.extract_prompt(post),
            tags=self.filter.extract_tags(post),
            url=f"https://reddit.com{post.permalink}",
            created_at=datetime.fromtimestamp(post.created_utc)
        )
```

#### 4.2.3 炼金模块

```python
# src/alchemist/gemini_client.py
import google.generativeai as genai
import os
import json
import random
import time
import logging
from typing import Dict, Any

from models.MUSICprompt_document import MUSICpromptDocument, DSPParameters, BilingualText
from models.raw_content import RawContent
from utils.rate_limiter import RateLimiter


class AlchemistAgent:
    """炼金�?Agent - 基于 Gemini 的内容处理器"""
    
    SYSTEM_PROMPT = """你是一个专业的音乐 Prompt 分析师。你的任务是将英文音�?Prompt 转换为标准化�?MUSICprompt 格式�?
请按以下步骤处理�?1. 将英文内容翻译为中文，保持专业术语的准确�?2. 根据 Prompt 内容推断合适的 DSP 参数（BPM、调性、能量等级等�?3. 生成适合抖音平台的中文标�?4. 提供一条专业的音频处理建议

输出格式必须是严格的 JSON�?""
    
    def __init__(self):
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.rate_limiter = RateLimiter(max_requests=15, window_seconds=60)
        self.logger = logging.getLogger(__name__)
    
    def process(self, raw_content: RawContent) -> MUSICpromptDocument:
        """处理原始内容，生�?MUSICprompt 文档"""
        self.rate_limiter.wait_if_needed()
        
        prompt = self._build_prompt(raw_content)
        response = self.model.generate_content(prompt)
        
        result = self._parse_response(response.text)
        
        return MUSICpromptDocument(
            id=f"MUSICprompt_{raw_content.id}",
            source=raw_content,
            title=BilingualText(en=raw_content.title, zh=result["title_zh"]),
            prompt=BilingualText(
                en=raw_content.prompt_text or "",
                zh=result["prompt_zh"]
            ),
            tags=raw_content.tags,
            douyin_tags=result["douyin_tags"],
            dsp_params=DSPParameters(**result["dsp_params"]),
            gem_suggestion=result["gem_suggestion"],
            viral_score=self._calculate_viral_score(raw_content, result)
        )
    
    def _build_prompt(self, raw_content: RawContent) -> str:
        """构建发送给 Gemini �?Prompt"""
        return f"""{self.SYSTEM_PROMPT}

输入内容�?标题：{raw_content.title}
Prompt：{raw_content.prompt_text}
标签：{', '.join(raw_content.tags)}
点赞数：{raw_content.upvotes}

请输�?JSON 格式的结果�?""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """解析 Gemini 响应"""
        import re
        import logging
        logger = logging.getLogger(__name__)
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失败: {e}")
                raise
        else:
            logger.error(f"未找到有�?JSON: {response_text[:200]}")
            raise ValueError("响应中未找到有效�?JSON 数据")
    
    def _calculate_viral_score(self, raw_content: RawContent, result: Dict) -> float:
        """计算爆款指数（量化公式）"""
        viral_score = min(
            0.4 * (raw_content.upvotes / 10) +           # 点赞权重 40%
            0.3 * len(result["douyin_tags"]) * 5 +       # 标签权重 30%
            0.3 * (len(result.get("prompt_zh", "")) / 100),  # 长度奖励 30%
            100
        )
        return round(viral_score, 1)
```

#### 4.2.4 视觉模块

```python
# src/herald/image_generator.py
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
import os
import logging

from models.MUSICprompt_document import MUSICpromptDocument


class ImageGenerator:
    """社交分享图片生成�?""
    
    CARD_SIZE = (1080, 1920)  # 小红�?抖音标准尺寸
    BACKGROUND_COLOR = "#1a1a2e"
    ACCENT_COLOR = "#e94560"
    TEXT_COLOR = "#ffffff"
    NOTO_FONT_PATH = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
    
    def __init__(self, template_dir: str = "assets/backgrounds"):
        self.template_dir = template_dir
        self.logger = logging.getLogger(__name__)
        self.font_path = self._find_font()
    
    def generate_viral_card(self, doc: MUSICpromptDocument, output_path: str) -> str:
        """生成爆款指数卡片"""
        # 创建画布
        img = Image.new('RGB', self.CARD_SIZE, self.BACKGROUND_COLOR)
        draw = ImageDraw.Draw(img)
        
        # 加载字体
        title_font = ImageFont.truetype(self.font_path, 48)
        score_font = ImageFont.truetype(self.font_path, 120)
        prompt_font = ImageFont.truetype(self.font_path, 32)
        
        # 绘制爆款指数
        score_text = f"{int(doc.viral_score)}%"
        score_bbox = draw.textbbox((0, 0), score_text, font=score_font)
        score_x = (self.CARD_SIZE[0] - score_bbox[2]) // 2
        draw.text((score_x, 200), score_text, fill=self.ACCENT_COLOR, font=score_font)
        
        # 绘制标题
        self._draw_wrapped_text(
            draw, doc.title.zh, 100, 400,
            self.CARD_SIZE[0] - 200, prompt_font, self.TEXT_COLOR
        )
        
        # 绘制 Prompt
        self._draw_wrapped_text(
            draw, doc.prompt.zh, 100, 800,
            self.CARD_SIZE[0] - 200, prompt_font, self.TEXT_COLOR
        )
        
        # 绘制标签
        tags_text = " ".join(f"#{tag}" for tag in doc.douyin_tags)
        draw.text((100, 1500), tags_text, fill=self.ACCENT_COLOR, font=prompt_font)
        
        # 绘制专业建议
        suggestion = f"💡 {doc.gem_suggestion}"
        self._draw_wrapped_text(
            draw, suggestion, 100, 1650,
            self.CARD_SIZE[0] - 200, prompt_font, "#888888"
        )
        
        # 保存图片
        img.save(output_path, quality=95)
        return output_path
    
    def _draw_wrapped_text(self, draw, text, x, y, max_width, font, fill):
        """绘制自动换行的文本（支持中英混合�?""
        lines = []
        current_line = ""
        
        for char in text:  # 逐字符处理，支持中文
            test_line = current_line + char
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] <= max_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = char
        lines.append(current_line)
        
        for i, line in enumerate(lines):
            draw.text((x, y + i * 50), line, fill=fill, font=font)
    
    def _find_font(self) -> str:
        """查找可用的中文字�?""
        font_paths = [
            self.NOTO_FONT_PATH,  # GitHub Actions 安装�?Noto CJK
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/System/Library/Fonts/PingFang.ttc",
            "C:\\Windows\\Fonts\\msyh.ttc",
        ]
        for path in font_paths:
            if os.path.exists(path):
                self.logger.info(f"使用字体: {path}")
                return path
        
        self.logger.warning("未找到中文字体，使用默认字体（中文可能无法正常显示）")
        try:
            return ImageFont.load_default()
        except Exception:
            return ""
```

#### 4.2.5 入口脚本

```python
# src/__main__.py
"""MUSICprompt Pipeline 主入�?""
import argparse
import logging
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def main():
    parser = argparse.ArgumentParser(description='MUSICprompt Pipeline')
    parser.add_argument('phase', choices=['all', 'scraper', 'alchemist', 'herald'],
                        default='all', help='执行阶段')
    args = parser.parse_args()
    
    if args.phase in ['all', 'scraper']:
        from scraper import run_scraper
        run_scraper()
    
    if args.phase in ['all', 'alchemist']:
        from alchemist import run_alchemist
        run_alchemist()
    
    if args.phase in ['all', 'herald']:
        from herald import run_herald
        run_herald()


if __name__ == "__main__":
    main()


# src/scraper/__main__.py
"""采集模块入口"""
from .reddit_client import RedditScraper
import logging

logger = logging.getLogger(__name__)


def run_scraper():
    scraper = RedditScraper()
    for subreddit in RedditScraper.TARGET_SUBREDDITS:
        posts = scraper.fetch_top_posts(subreddit)
        logger.info(f"�?r/{subreddit} 采集�?{len(posts)} 条内�?)


if __name__ == "__main__":
    run_scraper()


# src/alchemist/__main__.py
"""炼金模块入口"""
from .gemini_client import AlchemistAgent
from models.raw_content import RawContent
import json
import logging

logger = logging.getLogger(__name__)


def run_alchemist():
    with open("data/raw/latest.json", "r", encoding="utf-8") as f:
        raw_contents = [RawContent(**item) for item in json.load(f)]
    
    agent = AlchemistAgent()
    results = []
    for content in raw_contents:
        doc = agent.process(content)
        results.append(doc.model_dump())
        logger.info(f"处理完成: {doc.id}")
    
    with open("data/MUSICprompt_db.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    run_alchemist()


# src/herald/__main__.py
"""视觉模块入口"""
from .db_manager import DBManager
from .doc_renderer import DocRenderer
from .image_generator import ImageGenerator
import logging

logger = logging.getLogger(__name__)


def run_herald():
    db = DBManager()
    renderer = DocRenderer()
    img_gen = ImageGenerator()
    
    docs = db.get_all_documents()
    renderer.render_readme(docs)
    renderer.render_categories(docs)
    
    for doc in docs[:5]:  # 只为�?5 个生成图�?        img_gen.generate_viral_card(doc, f"assets/cards/{doc.id}.png")
        logger.info(f"生成图片: {doc.id}")


if __name__ == "__main__":
    run_herald()
```

#### 4.2.6 README 模板

```jinja2
{# templates/readme.md.j2 #}
# MUSICprompt - 海外音频情报中转�?
> ⚠️ **免责声明**
> 
> 本项目数据源�?Reddit 社区公开内容，仅供学习研究使用，**禁止商用**�?> 所有内容的版权归原作者所有。如需删除某条内容，请提交 Issue�?> 
> 本项目不�?AI 生成�?DSP 参数建议的准确性负责，实际使用请结合专业判断�?
---

## 📊 今日爆款 Prompt

| 排名 | 标题 | 爆款指数 | 标签 | 来源 |
|:---:|------|:-------:|------|------|
{% for doc in docs[:10] %}
| {{ loop.index }} | {{ doc.title.zh }} | {{ doc.viral_score }}% | {{ doc.douyin_tags[:3] | join(' ') }} | [原文]({{ doc.source.url }}) |
{% endfor %}

---

## 📁 数据结构

每个 Prompt 包含以下信息�?
- **双语标题**: 中英文对�?- **双语 Prompt**: 完整的提示词翻译
- **DSP 参数**: BPM、调性、能量等级等
- **抖音标签**: 本土化热门标�?- **专业建议**: AI 生成的音频处理建�?
---

## 🔗 相关链接

- [完整数据库](data/MUSICprompt_db.json)
- [分类索引](docs/categories/)
- [社交图片](assets/cards/)

---

*最后更�? {{ updated_at }}*
*数据来源: Reddit r/SunoAI, r/Udio, r/aiMusic*
```

### 4.3 GitHub Actions 工作�?
```yaml
# .github/workflows/daily-pipeline.yml
name: MUSICprompt Daily Pipeline

on:
  schedule:
    - cron: '0 0 * * *'  # UTC 00:00 = 北京时间 08:00
  workflow_dispatch:      # 支持手动触发

env:
  PYTHON_VERSION: '3.11'

jobs:
  pipeline:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}
          cache: 'pip'
      
      - name: Install Chinese fonts
        run: sudo apt-get update && sudo apt-get install -y fonts-noto-cjk
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]
      
      - name: Run tests with coverage
        run: |
          pytest --cov=src --cov-report=xml --cov-fail-under=80
        continue-on-error: true
      
      - name: Run Phase 1 - Scraping
        env:
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
        run: python -m src.scraper
      
      - name: Run Phase 2 - Alchemist
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: python -m src.alchemist
      
      - name: Run Phase 3 - Herald
        run: python -m src.herald
      
      - name: Commit and Push changes
        run: |
          git config --local user.email "github-actions[bot]@users.noreply.github.com"
          git config --local user.name "github-actions[bot]"
          git add -A
          git diff --quiet && git diff --staged --quiet || git commit -m "chore: daily update [skip ci]"
          git push
      
      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: daily-output
          path: |
            data/MUSICprompt_db.json
            assets/cards/
          retention-days: 30
```

---

## 5. 数据流程与协�?
### 5.1 MUSICprompt 数据协议规范

#### 5.1.1 协议版本

当前版本：`v1.0.0`

#### 5.1.2 JSON Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://MUSICprompt.dev/schemas/document.json",
  "title": "MUSICprompt Document",
  "description": "MUSICprompt 标准文档格式",
  "type": "object",
  "required": ["id", "version", "source", "title", "prompt", "dsp_params", "viral_score"],
  "properties": {
    "id": {
      "type": "string",
      "pattern": "^MUSICprompt_[a-z0-9]+$",
      "description": "文档唯一标识"
    },
    "version": {
      "type": "string",
      "pattern": "^\\d+\\.\\d+\\.\\d+$",
      "default": "1.0.0",
      "description": "协议版本�?
    },
    "source": {
      "type": "object",
      "description": "原始来源信息",
      "properties": {
        "platform": {"type": "string", "enum": ["reddit", "twitter", "discord"]},
        "url": {"type": "string", "format": "uri"},
        "author": {"type": "string"},
        "collected_at": {"type": "string", "format": "date-time"}
      }
    },
    "title": {
      "type": "object",
      "description": "双语标题",
      "properties": {
        "en": {"type": "string"},
        "zh": {"type": "string"}
      }
    },
    "prompt": {
      "type": "object",
      "description": "双语 Prompt",
      "properties": {
        "en": {"type": "string"},
        "zh": {"type": "string"}
      }
    },
    "tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "原始风格标签"
    },
    "douyin_tags": {
      "type": "array",
      "items": {"type": "string"},
      "description": "抖音平台标签"
    },
    "dsp_params": {
      "type": "object",
      "description": "DSP 参数",
      "properties": {
        "bpm": {"type": "integer", "minimum": 40, "maximum": 220},
        "key": {"type": "string"},
        "energy_level": {"type": "string", "enum": ["low", "medium", "high", "very_high"]},
        "frequency_center": {"type": "string"},
        "dynamics_range": {"type": "string"}
      }
    },
    "gem_suggestion": {
      "type": "string",
      "description": "Gem 专业建议"
    },
    "viral_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "爆款指数"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```

#### 5.1.3 示例文档

```json
{
  "id": "MUSICprompt_abc123",
  "version": "1.0.0",
  "source": {
    "platform": "reddit",
    "url": "https://reddit.com/r/SunoAI/comments/abc123",
    "author": "music_lover_2024",
    "collected_at": "2026-03-23T08:00:00Z"
  },
  "title": {
    "en": "Epic Cinematic Trailer Music",
    "zh": "史诗级电影预告片配乐"
  },
  "prompt": {
    "en": "Epic orchestral trailer music with powerful drums, soaring strings, and dramatic brass. Building tension leading to an explosive climax. Perfect for movie trailers and game intros.",
    "zh": "史诗级管弦乐预告片配乐，配有强有力的鼓点、高亢的弦乐和戏剧性的铜管。层层递进的张力最终爆发至高潮。非常适合电影预告片和游戏开场�?
  },
  "tags": ["cinematic", "orchestral", "epic", "trailer"],
  "douyin_tags": ["史诗�?, "电影配乐", "燃爆", "氛围�?],
  "dsp_params": {
    "bpm": 120,
    "key": "D Minor",
    "energy_level": "very_high",
    "frequency_center": "200Hz-2kHz",
    "dynamics_range": "Wide (40dB)"
  },
  "gem_suggestion": "建议在混音时切掉 30Hz 以下的低频，避免底鼓与贝斯产生浑浊感。铜管组建议�?2-4kHz 做适度提升以增加穿透力�?,
  "viral_score": 92.5,
  "created_at": "2026-03-23T08:15:00Z",
  "updated_at": "2026-03-23T08:15:00Z"
}
```

### 5.2 数据流转�?
```
┌─────────────────────────────────────────────────────────────────────────────�?�?                          数据流转全景�?                                    �?├─────────────────────────────────────────────────────────────────────────────�?�?                                                                            �?�? ┌─────────�?                                                               �?�? �?Reddit  �?                                                               �?�? �? API    �?                                                               �?�? └────┬────�?                                                               �?�?      �?JSON Response                                                       �?�?      �?                                                                    �?�? ┌─────────�?    ┌─────────�?    ┌─────────�?                              �?�? �? Raw    │────▶│ Filter  │────▶│ Dedup   �?                              �?�? �? Data   �?    �?Engine  �?    �?Engine  �?                              �?�? └─────────�?    └─────────�?    └────┬────�?                              �?�?                                      �?                                    �?�?                                      �?RawContent[]                        �?�?                                      �?                                    �?�? ┌─────────────────────────────────────────────────────────────────────�?  �?�? �?                       Alchemist Agent                               �?  �?�? �? ┌─────────�?    ┌─────────�?    ┌─────────�?    ┌─────────�?      �?  �?�? �? │Translate│────▶│DSP Infer│────▶│Tag Gen  │────▶│Suggestion�?     �?  �?�? �? �?Engine  �?    �?Engine  �?    �?Engine  �?    �?Engine  �?      �?  �?�? �? └─────────�?    └─────────�?    └─────────�?    └─────────�?      �?  �?�? └─────────────────────────────────────────────────────────────────────�?  �?�?                                      �?                                    �?�?                                      �?MUSICpromptDocument[]                      �?�?                                      �?                                    �?�? ┌─────────�?    ┌─────────�?    ┌─────────�?                              �?�? �? JSON   │────▶│  MD     │────▶│  PNG    �?                              �?�? �?  DB    �?    �? Docs   �?    �? Cards  �?                              �?�? └─────────�?    └─────────�?    └─────────�?                              �?�?      �?              �?              �?                                    �?�?      └───────────────┴───────────────�?                                    �?�?                      �?                                                    �?�?                      �?                                                    �?�?               ┌─────────�?                                                 �?�?               �?  Git   �?                                                 �?�?               �? Push   �?                                                 �?�?               └─────────�?                                                 �?�?                                                                            �?└─────────────────────────────────────────────────────────────────────────────�?```

---

## 6. 部署架构

### 6.1 部署拓扑�?
```
┌─────────────────────────────────────────────────────────────────────────────�?�?                          部署架构�?                                        �?├─────────────────────────────────────────────────────────────────────────────�?�?                                                                            �?�?                        ┌─────────────────�?                                �?�?                        �? GitHub Actions �?                                �?�?                        �?  (Runner)      �?                                �?�?                        �? ┌───────────�? �?                                �?�?                        �? �?Scheduler �? �?                                �?�?                        �? �?(Cron)    �? �?                                �?�?                        �? └─────┬─────�? �?                                �?�?                        �?       �?       �?                                �?�?                        �? ┌─────▼─────�? �?                                �?�?                        �? �?Pipeline  �? �?                                �?�?                        �? �?Executor  �? �?                                �?�?                        �? └─────┬─────�? �?                                �?�?                        └────────┼────────�?                                �?�?                                 �?                                         �?�?             ┌───────────────────┼───────────────────�?                     �?�?             �?                  �?                  �?                     �?�?             �?                  �?                  �?                     �?�?    ┌────────────────�? ┌────────────────�? ┌────────────────�?            �?�?    �? Reddit API    �? �? Gemini API    �? �?GitHub Repo    �?            �?�?    �? (External)    �? �? (External)    �? �?(Storage)      �?            �?�?    �?               �? �?               �? �?               �?            �?�?    �? - r/SunoAI    �? �? - Translate   �? �? - JSON DB     �?            �?�?    �? - r/Udio      �? �? - DSP Infer   �? �? - Markdown    �?            �?�?    �? - r/aiMusic   �? �? - Tag Gen     �? �? - Images      �?            �?�?    └────────────────�? └────────────────�? └────────────────�?            �?�?                                                                            �?└─────────────────────────────────────────────────────────────────────────────�?```

### 6.2 环境配置

#### 6.2.1 GitHub Secrets 配置

| Secret 名称 | 用�?| 获取方式 |
|------------|------|---------|
| `REDDIT_CLIENT_ID` | Reddit API 客户�?ID | https://www.reddit.com/prefs/apps |
| `REDDIT_CLIENT_SECRET` | Reddit API 客户端密�?| 同上 |
| `GEMINI_API_KEY` | Gemini API 密钥 | https://makersuite.google.com/app/apikey |

#### 6.2.2 环境变量配置

```bash
# .env.example

# Reddit API 配置
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret

# Gemini API 配置
GEMINI_API_KEY=your_gemini_api_key

# 可选配�?MIN_UPVOTES=50
MAX_POSTS_PER_RUN=50
VIRAL_SCORE_THRESHOLD=70
```

### 6.3 资源消耗预�?
| 资源类型 | 预估消�?| 免费额度 | 是否充足 |
|---------|---------|---------|---------|
| GitHub Actions 分钟�?| ~10 分钟/�?| 2000 分钟/�?| �?充足 |
| Gemini API 调用 | ~50 �?�?| 1500 �?�?| �?充足 |
| 存储空间 | ~10 MB/�?| 1 GB | �?充足 |
| 带宽 | ~50 MB/�?| 100 GB/�?| �?充足 |

---

## 7. 风险评估与应对策�?
### 7.1 风险矩阵

```
                    影响程度
              �?          �?          �?         ┌─────────┬─────────┬─────────�?    �?  �?        �?API风控 �?版权风险 �?�?      �?        �?  ⚠️    �?  🔴    �?�?      ├─────────┼─────────┼─────────�?�?      �?        �?        �?平台依赖 �?�?   �?�?        �?同质�? �?  ⚠️    �?         �?        �?  ⚠️    �?        �?         ├─────────┼─────────┼─────────�?    �?  �?        �?        �?数据质量 �?         �?        �?        �?  🟡    �?         └─────────┴─────────┴─────────�?
图例：�?高风�? ⚠️ 中风�? 🟡 低风�?```

### 7.2 详细风险分析

#### 7.2.1 API 额度风控风险

| 维度 | 描述 |
|-----|------|
| **风险描述** | Gemini API 虽有免费额度，但短时间内高频请求可能触发风控，导�?API 暂时封禁 |
| **触发条件** | 请求频率超过 15 �?分钟，或单日请求量异常激�?|
| **影响范围** | Phase 2 炼金阶段无法执行，流水线中断 |
| **发生概率** | 中等 |
| **影响程度** | �?|

**应对策略**�?
```python
# 速率限制实现
class RateLimiter:
    def __init__(self, max_requests: int = 15, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def wait_if_needed(self):
        now = time.time()
        self.requests = [r for r in self.requests if now - r < self.window_seconds]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.window_seconds - (now - self.requests[0])
            sleep_time += random.uniform(1, 5)  # 随机抖动
            time.sleep(sleep_time)
        
        self.requests.append(now)
```

#### 7.2.2 内容同质化风�?
| 维度 | 描述 |
|-----|------|
| **风险描述** | 类似项目增多，导�?GitHub 上出现大量雷同的翻译项目，降低差异化竞争优势 |
| **触发条件** | 项目公开后，思路被他人复�?|
| **影响范围** | 项目独特性下降，用户关注度降�?|
| **发生概率** | 中等 |
| **影响程度** | �?|

**应对策略**�?
1. **差异化价�?*：每�?Prompt 附带专业 DSP 建议，形�?专家润色"的品牌认�?2. **持续创新**：定期更新算法模型，引入新的价值维�?3. **社区运营**：建立用户社群，增强用户粘�?
#### 7.2.3 版权法律风险

| 维度 | 描述 |
|-----|------|
| **风险描述** | 直接搬运 Reddit 内容可能涉及版权纠纷，原作者可能主张著作权 |
| **触发条件** | 原作者发现并提出异议，或项目商业化后引发争议 |
| **影响范围** | 项目声誉受损，可能面临法律诉�?|
| **发生概率** | �?|
| **影响程度** | �?|

**应对策略**�?
1. **免责声明**：在 README 显著位置标注
   ```markdown
   > ⚠️ **免责声明**
   > 本项目数据源�?Reddit 社区公开内容，仅供学习研究使用，禁止商用�?   > 所有内容的版权归原作者所有。如需删除，请提交 Issue�?   ```

2. **来源追溯**：每条数据保留原始链接，增加透明�?3. **非商业定�?*：明确项目为开源学习项目，不涉及商业利�?
#### 7.2.4 平台依赖风险

| 维度 | 描述 |
|-----|------|
| **风险描述** | 项目高度依赖 GitHub Actions �?Gemini API，一旦平台政策变更，工作流可能中�?|
| **触发条件** | Google 修改 Gemini 免费政策，或 GitHub 限制 Actions 使用 |
| **影响范围** | 整个流水线无法运�?|
| **发生概率** | �?|
| **影响程度** | �?|

**应对策略**�?
1. **多云备份**：准�?GitLab CI、Cloudflare Workers 等替代方�?2. **模型备�?*：保�?OpenAI、Claude 等其�?LLM 的接口适配
3. **本地运行**：支持本�?CLI 运行，不依赖云端

---

## 8. 系统局限性分�?
### 8.1 已知局限�?
| 局限�?| 描述 | 影响程度 | 可解决�?|
|-------|------|---------|---------|
| **实时性滞�?* | 定时任务运行，无法捕捉分钟级流量爆发 | �?| 部分可解�?|
| **听感验证缺失** | AI 推断的参数未经实际音频验�?| �?| 需人工介入 |
| **平台依赖** | 依赖外部平台，存在单点故障风�?| �?| 可缓�?|
| **语言质量** | 机器翻译可能存在专业术语偏差 | �?| 可优�?|
| **数据完整�?* | 部分帖子可能被删除或编辑 | �?| 无法避免 |

### 8.2 局限性详细分�?
#### 8.2.1 实时性滞�?
**问题描述**�?
系统采用定时任务模式（每日运行一次），无法捕捉实时的流量爆发。当某个 Prompt �?Reddit 上突然爆火时，系统可能需要等待最�?24 小时才能采集到�?
**影响分析**�?
- 错过最�?蹭热�?时间窗口
- 用户获取信息存在延迟
- 竞争对手可能更快响应

**缓解方案**�?
```yaml
# 增加运行频率
on:
  schedule:
    - cron: '0 */6 * * *'  # �?6 小时运行一�?    - cron: '0 0 * * *'    # 完整运行（每日）
```

#### 8.2.2 听感验证缺失

**问题描述**�?
Gemini 生成�?DSP 参数是基于文本推断的"伪参�?，未经实际音频验证。可能存�?词不达意"的情况，即参数描述与实际听感不符�?
**影响分析**�?
- 用户按照参数调整后，效果可能不如预期
- 降低专业可信�?- 可能误导初学�?
**缓解方案**�?
1. **标注说明**：明确标注参数为"AI 推断建议"
2. **用户反馈**：引入用户评分机制，收集实际使用反馈
3. **专家审核**：对高分内容进行人工审核

---

## 9. 未来拓展规划

### 9.1 拓展路线�?
```
┌─────────────────────────────────────────────────────────────────────────────�?�?                          产品演进路线�?                                    �?├─────────────────────────────────────────────────────────────────────────────�?�?                                                                            �?�? Phase 1 (当前)          Phase 2            Phase 3           Phase 4     �?�? ┌─────────�?        ┌─────────�?       ┌─────────�?      ┌─────────�?    �?�? �?基础流水线│ ──────▶│ 自媒�? �?──────▶│ Web �? �?────▶│ 多平�? �?    �?�? �?        �?        �?合成�? �?       �?预测�? �?      �?适配�? �?    �?�? └─────────�?        └─────────�?       └─────────�?      └─────────�?    �?�?    Q1 2026            Q2 2026            Q3 2026           Q4 2026      �?�?                                                                            �?�? 功能�?               功能�?             功能�?            功能�?       �?�? - Reddit 采集         - FFmpeg 集成       - Streamlit Web   - 腾讯 SongGen�?�? - Gemini 处理         - 视频自动合成      - 实时检�?       - AudioCraft  �?�? - 自动部署            - 一键发�?         - 优化建议        - 多平台参�? �?�?                                                                            �?└─────────────────────────────────────────────────────────────────────────────�?```

### 9.2 拓展功能详细设计

#### 9.2.1 自媒体素材自动合成器

**功能描述**�?
拓展一�?Agent，自动调�?FFmpeg，将生成的音�?Prompt 配上"协议 DNA 图片"，直接合�?15 秒预览短视频，用户只需点击"发布"即可�?
**技术方�?*�?
```python
# 视频合成模块伪代�?class VideoComposer:
    def compose(self, doc: MUSICpromptDocument, audio_path: str) -> str:
        # 1. 生成动态背�?        background = self.generate_background(doc.dsp_params)
        
        # 2. 叠加文字动画
        text_overlay = self.create_text_animation(doc.title.zh)
        
        # 3. 合成视频
        output = f"output/{doc.id}.mp4"
        ffmpeg.compose(
            background=background,
            overlay=text_overlay,
            audio=audio_path,
            duration=15,
            output=output
        )
        return output
```

**预期效果**�?
- 自动生成小红�?抖音风格的短视频
- 包含 Prompt 文字、爆款指数、标签等信息
- 支持一键下载或直接发布

#### 9.2.2 Web 端爆款预测器

**功能描述**�?
当仓�?Star 足够多后，开发一个简单的 Web 页面（使�?Streamlit），让用户输入一句话，Agent 实时�?MUSICprompt 库中检索最接近的爆款基因，并给出优化方案�?
**技术方�?*�?
```python
# Streamlit Web 应用伪代�?import streamlit as st
from sentence_transformers import SentenceTransformer

class ViralPredictor:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.db = self.load_MUSICprompt_db()
        self.embeddings = self.compute_embeddings()
    
    def predict(self, user_input: str) -> List[MUSICpromptDocument]:
        input_embedding = self.model.encode(user_input)
        similarities = cosine_similarity([input_embedding], self.embeddings)
        top_indices = similarities.argsort()[-5:][::-1]
        return [self.db[i] for i in top_indices]
    
    def suggest_optimization(self, user_input: str, similar_docs: List) -> str:
        # 调用 Gemini 生成优化建议
        pass

# Streamlit 界面
st.title("🎵 MUSICprompt 爆款预测�?)
user_input = st.text_input("输入你的音乐创意...")
if st.button("预测"):
    predictor = ViralPredictor()
    results = predictor.predict(user_input)
    st.write("相似爆款 Prompt�?, results)
```

**预期效果**�?
- 用户输入创意描述
- 系统返回相似度最高的爆款 Prompt
- 提供优化建议

#### 9.2.3 多模型分流适配�?
**功能描述**�?
目前仅支�?Suno/Udio，未来可扩展支持腾讯 SongGeneration、AudioCraft 等多平台，做�?全平台适配�?�?
**技术方�?*�?
```python
# 多平台适配器伪代码
from abc import ABC, abstractmethod

class PromptAdapter(ABC):
    @abstractmethod
    def adapt(self, MUSICprompt_doc: MUSICpromptDocument) -> str:
        pass

class SunoAdapter(PromptAdapter):
    def adapt(self, doc: MUSICpromptDocument) -> str:
        return f"{doc.prompt.en} [Style: {', '.join(doc.tags)}]"

class UdioAdapter(PromptAdapter):
    def adapt(self, doc: MUSICpromptDocument) -> str:
        return f"Prompt: {doc.prompt.en}\nTags: {', '.join(doc.tags)}"

class TencentSongGenAdapter(PromptAdapter):
    def adapt(self, doc: MUSICpromptDocument) -> str:
        # 腾讯 SongGeneration 特定格式
        return json.dumps({
            "lyrics": doc.prompt.zh,
            "style": doc.tags,
            "bpm": doc.dsp_params.bpm
        }, ensure_ascii=False)

class AdapterFactory:
    ADAPTERS = {
        "suno": SunoAdapter,
        "udio": UdioAdapter,
        "tencent": TencentSongGenAdapter,
    }
    
    @classmethod
    def get_adapter(cls, platform: str) -> PromptAdapter:
        return cls.ADAPTERS[platform]()
```

**预期效果**�?
- 一�?Prompt，多平台适配
- 用户可选择目标平台
- 自动生成平台特定格式

---

## 10. 附录

### 10.1 术语�?
| 术语 | 全称 | 解释 |
|-----|------|------|
| MUSICprompt | Viral Music DNA Protocol | 爆款音乐基因协议 |
| DSP | Digital Signal Processing | 数字信号处理 |
| Prompt | - | 提示词，AI 音乐生成的输入文�?|
| LLM | Large Language Model | 大语言模型 |
| CI/CD | Continuous Integration/Continuous Deployment | 持续集成/持续部署 |

### 10.2 参考链�?
- [Reddit API Documentation](https://www.reddit.com/dev/api)
- [PRAW Documentation](https://praw.readthedocs.io/)
- [Gemini API Documentation](https://ai.google.dev/docs)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Pillow Documentation](https://pillow.readthedocs.io/)

### 10.3 变更日志

| 版本 | 日期 | 变更内容 | 作�?|
|-----|------|---------|------|
| v1.0.1 | 2026-03-23 | 根据审批意见完成8处必须修�?3处建议优�?| MUSICprompt Team |
| v1.0.0 | 2026-03-23 | 初始版本 | MUSICprompt Team |

### 10.4 审批记录

| 角色 | 姓名 | 审批状�?| 日期 | 备注 |
|-----|------|---------|------|------|
| 技术负责人 | | 已通过 | 2026-03-23 | 条件通过，已完成全部修改 |
| 产品负责�?| | 已通过 | 2026-03-23 | 免责声明已确�?|
| 项目经理 | | 已通过 | 2026-03-23 | 预计 2026-03-25 上线 |

---

**文档结束**

*本文档由 MUSICprompt 项目组编写，如有疑问请联系项目负责人�?
