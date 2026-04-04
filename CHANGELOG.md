# Changelog

All notable changes to this project will be documented in this file.
Format based on [Keep a Changelog](https://keepachangelog.com/).

## [1.4.0] - 2026-04-04

### 🚀 Added

- **Prompt 内容检测系统 v2** (`is_real_prompt()` 完全重写)
  - 基于真实 Suno Prompt 格式研究（参考 Suno V5 官方指南 + 社区最佳实践）
  - **Layer 1 正信号检测**（必须 ≥2 分）:
    - 结构元标签 `[Intro]`, `[Verse]`, `[Chorus]` 等 (3分)
    - 组合标签 `[Verse][Male][Whispered]` (3分)
    - BPM 标记 `118 BPM` / `bpm:120` (2分)
    - 分享引导词 `"my prompt:"`, `"here's my..."`, `"I used:"` (2分)
    - Suno 风格密集标签串 `rock pop, guitar, distorted, ...` (2分)
    - 调性标记 `key: C major` (1分)
  - **Layer 2 负信号扣分**（讨论/散文/吐槽特征）:
    - 第一人称叙事密度 ("I have been", "my experience"...) — ≥4处 -3分
    - 吐槽/抱怨词 ("awful", "magic wand", "ruining"...) — ≥2处 -2分
    - 净分 < 1 则拦截
  - **Layer 3 格式门槛**: ≥5 个逗号

### 🐛 Fixed

- **Magic Wand 类吐槽帖**: "The new personalize magic wand for styles is awful" → 被负信号层拦截
- **含 'prompt' 词的讨论帖**: "What prompt settings do you use?" → 无正信号，被拦截
- **个人散文**: Pearls 长文 → 无正信号 + 高第一人称密度，被拦截

### 📊 Verified

5 条测试数据验证:
```
Magic Wand 吐槽   → REJECT (无正信号 + awful/ruining 负信号)
Pearls 散文        → REJECT (无正信号 + 第一人称过密)
讨论帖             → REJECT (垃圾标题 + 无正信号)
真实结构化 Prompt   → PASS  (9.5分, [Intro][Verse][Chorus])
真实风格 Prompt     → PASS  (8.3分, lo-fi/Rhodes/85 BPM)
```

---

## [1.3.0] - 2026-04-04

### 🐛 Fixed

- **爬虫硬性门槛**: 新增 `is_real_prompt()` 硬性过滤
  - 必须包含 `prompt` 关键词（不区分大小写）
  - 正文必须有 ≥5 个英文或中文逗号（结构化内容标志）
  - 彻底拦截个人散文、项目介绍、纯讨论等非 Prompt 内容
  - 过滤流水线升级为 5 步: 硬性门槛 → 垃圾帖检测 → 质量评分 → 阈值 → 排序

### 🔧 Changed

- 版本号策略改为语义化版本号 (`x.y.z`)

---

## [1.2.0] - 2026-04-04

### 🚀 Added

- **Prompt 质量检测系统** (`reddit_fetcher.py`)
  - `is_junk_post()`: 17 种垃圾标题模式一票否决（help/how/why/bug/error/question 等）
  - `calc_prompt_score()`: Prompt 质量评分 0~10（结构标签 35% + 技术参数 15% + 关键词 15% + 方括号 20% + 长度 15%）
  - `filter_and_score_posts()`: 4 步过滤流水线
  - `_fetch_via_json()`: JSON API 作为 RSS 的 fallback（CI 环境可用）

### 🐛 Fixed

- **点赞数排序失效**: RSS 无法可靠提取 score，改用 Prompt 质量评分作为主排序依据
- **垃圾帖泛滥**: 求助/问题/Bug 报告/分享帖被正确识别并过滤

### 📊 Verified

测试数据验证 (7 条模拟帖子):
```
输入: 7 条
├── 3 垃圾帖 (help/bug/question) → is_junk_post() 拦截
├── 2 低质量帖 (<4.0 分) → score threshold 淘汰
└── 2 高质量 Prompt 保留 (9.1分 / 7.0分)
```

---

## [1.1.0] - 2026-04-04

### 🚀 Added

- **`src/config.py`** — 统一配置管理模块
  - 6 个配置类: `RedditConfig`, `PipelineConfig`, `LLMConfig`, `DatabaseConfig`, `OutputConfig`, `GitHubSourceConfig`
  - 支持环境变量覆盖 + `.env` 文件自动加载

- **`src/constants.py`** — 共享常量定义模块
  - `GENRE_ICONS`, `USE_CASE_NAMES`, `MUSIC_KEYWORDS`, `TECH_KEYWORDS`, `INSTRUMENTS`, `GENRES`, `STRUCTURE_TAGS`, `SCENARIO_MAP`
  - 消除跨文件重复定义

- **`.env.template`** — 环境变量配置模板

### 🔧 Changed

#### Reddit 爬虫 (`tools/reddit_fetcher.py`)
- 废弃: `urllib` JSON API（Reddit OAuth 403）
- 新增: `feedparser` RSS Feed 方案（无需认证）

#### 数据库层 (`src/db/models.py`)
- FTS5 全文搜索替代 `LIKE '%keyword%'`
- 连接复用 + WAL 模式 + 外键约束
- 新增 `@contextmanager connection()` 接口

#### 去重 (多文件)
- `sync_to_markdown.py`, `output_formatter.py`, `auto_pipeline.py`, `prompt_extractor.py`
- 所有硬编码常量/路径统一引用 `src.constants` / `src.config`

#### CI/CD (`.github/workflows/daily-fetcher.yml`)
- 适配 RSS 方案 + Repository Variables 注入

#### 依赖 (`requirements.txt`)
- 新增 `feedparser>=6.0.0`, `requests>=2.31.0`

### 🐛 Fixed

- Reddit 爬虫 403 错误（RSS 方案解决）
- 全文搜索性能 O(n) → O(log n)

---

## [1.0.0] - Initial Release

Initial release with basic prompt extraction, LLM translation, and Markdown output pipeline.
