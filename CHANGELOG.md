# Changelog

All notable changes to this project will be documented in this file.

## [2.0.0] - 2026-04-04

### 🚀 新增 (Added)

- **`src/config.py`** — 统一配置管理模块
  - 集中管理所有配置项（Reddit、流水线、LLM、数据库、输出、GitHub 数据源）
  - 支持环境变量覆盖，支持 `.env` 文件自动加载
  - 类型安全的配置类：`RedditConfig`, `PipelineConfig`, `LLMConfig`, `DatabaseConfig`, `OutputConfig`, `GitHubSourceConfig`

- **`src/constants.py`** — 共享常量定义模块
  - `GENRE_ICONS`: 流派图标映射（24 个流派 emoji）
  - `USE_CASE_NAMES`: 使用场景中英文名称映射
  - `MUSIC_KEYWORDS`: 音乐关键词列表（用于数据清洗过滤）
  - `TECH_KEYWORDS`, `INSTRUMENTS`, `GENRES`, `STRUCTURE_TAGS`, `SCENARIO_MAP`
  - 消除跨文件重复定义，统一维护

- **`.env.template`** — 环境变量配置模板
  - 包含所有可配置项的说明和默认值
  - 支持 LLM API Key、Reddit 爬虫参数、数据处理阈值等

### 🔧 变更 (Changed)

#### Reddit 爬虫重写 (`tools/reddit_fetcher.py`)
- **废弃**: 原基于 `urllib` 的 Reddit JSON API 方案（已被 Reddit 2023 OAuth 政策拦截，返回 403）
- **新增**: 基于 `feedparser` 的 RSS Feed 方案
  - 无需 OAuth 认证，无需 API Key
  - 使用 Reddit 公开 RSS 接口: `https://www.reddit.com/r/{subreddit}/.rss`
  - 新增 HTML 清理、点赞数正则提取、作者解析等辅助函数
  - 配置项通过 `config.reddit.*` 统一管理

#### 数据库层升级 (`src/db/models.py`)
- **FTS5 全文搜索**: `search()` 方法从 `LIKE '%keyword%'` 升级为 FTS5 `MATCH` 查询
  - 主路径使用 `JOIN prompts_fts` + `ORDER BY rank` 高效检索
  - 保留 LIKE 作为 fallback 兼容无结果场景
  - FTS5 虚拟表增加 `tokenize='unicode61'` 分词器支持中文
- **连接管理优化**:
  - 新增 `_conn` 连接复用机制，避免频繁创建/销毁连接
  - 新增 `@contextmanager connection()` 上下文管理器接口
  - 启用 WAL 日志模式和外键约束 (`PRAGMA journal_mode=WAL`, `PRAGMA foreign_keys=ON`)
  - `db_path` 参数支持从 config 默认值获取

#### 配置与常量去重 (多文件)
- `tools/sync_to_markdown.py`: 移除本地 `GENRE_ICONS` / `USE_CASE_NAMES` 定义，改用 `src.constants`
- `tools/output_formatter.py`: 同上，移除本地硬编码的 `USE_CASE_NAMES` 和 `use_case_names` 字典
- `tools/auto_pipeline.py`:
  - `SOURCES` 列表改为从 `app_config.github.SOURCES` 动态加载
  - `DataCleaner.MUSIC_KEYWORDS` 改用共享 `MUSIC_KEYWORDS`
  - `MIN_PROMPT_LENGTH` / `MAX_PROMPT_LENGTH` 从配置读取
  - 所有硬编码路径替换为 `app_config.*` 引用
- `tools/prompt_extractor.py`:
  - `PromptQualityScorer` 内部 4 组关键词列表全部引用 `src.constants`
  - `scenario_map` 字典引用共享 `SCENARIO_MAP`

#### GitHub Actions 工作流更新 (`.github/workflows/daily-fetcher.yml`)
- 步骤名称从 "Fetch Reddit Posts" 更新为 "Fetch Reddit Posts (RSS Feed)"
- 配置通过 GitHub Repository Variables 注入（`REDDIT_SUBREDDITS`, `MIN_UPVOTES`, `TARGET_COUNT`）
- Issue 标签增加 `rss-feed` 标识
- Fallback Issue 内容适配 RSS 方案的错误提示

#### 依赖更新 (`requirements.txt`)
- 新增 `feedparser>=6.0.0`（RSS 解析）
- 新增 `requests>=2.31.0`（HTTP 客户端备用）
- 保留原有依赖不变

### 🐛 修复 (Fixed)

- **Reddit 爬虫 403 错误**: 原 JSON API 方案因 Reddit 强制 OAuth 导致完全不可用，RSS 方案彻底解决此问题
- **搜索性能**: 全文搜索从 O(n) LIKE 扫描升级为 O(log n) FTS5 索引查询
- **连接泄漏风险**: 数据库连接复用减少 I/O 开销

### 📝 迁移指南 (Migration)

1. 安装新依赖:
   ```bash
   pip install feedparser requests
   ```

2. 复制环境变量模板:
   ```bash
   cp .env.template .env
   # 编辑 .env 填入你的 API Keys
   ```

3. 如有自定义 GitHub Actions 配置，在仓库 Settings → Variables 中添加:
   - `REDDIT_SUBREDDITS` (可选, 默认 `SunoAI,Udio,aiMusic`)
   - `MIN_UPVOTES` (可选, 默认 `50`)
   - `TARGET_COUNT` (可选, 默认 `7`)

4. 已有数据库无需迁移，FTS5 表和触发器会在下次 `init_db()` 时自动创建（`CREATE TABLE IF NOT EXISTS`）

---

## [1.x] - Earlier Releases

Initial release with basic prompt extraction, LLM translation, and Markdown output pipeline.
