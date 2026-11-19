# MUSICprompt

面向 AI 音乐创作的开源 Prompt 数据集、检索工具与确定性 Prompt 编译器。

v2 的重点不是单纯增加文本数量，而是让数据**可审查、可迁移、可检索、可验证**：区分原始参数与模型推断，区分文本质量与实际生成效果。

## 当前数据

<!-- AUTO_STATS:START -->
| 指标 | 当前值 |
|---|---:|
| 不重复 Prompt | 283 |
| 文本质量分 ≥ 8 | 95 |
| 有明确 BPM | 49 |
| 有明确调性 | 23 |
| 已完成生成验证 | 0 |
| 平均文本质量分 | 7.44 |
<!-- AUTO_STATS:END -->

## 快速开始

```bash
python -m pip install -r requirements.txt
python tools/build.py
```

`build.py` 会从统一事实数据生成 SQLite、CSV、网站数据、统计信息，并检查主要文档链接。

### 搜索 Prompt

```bash
python tools/search_prompts.py --query "electronic"
python tools/search_prompts.py --genre pop --min-score 8
python tools/search_prompts.py --use-case party
python tools/search_prompts.py --stats
```

也可以直接打开 [检索网站](web/index.html)，或在仓库根目录运行：

```bash
python -m http.server 8000 --directory web
```

然后访问 `http://localhost:8000`。

### 从一句话生成 Prompt

```bash
python tools/compose_prompt.py \
  --text "雨夜开车，克制但逐渐释放的中文独立流行，96 BPM，钢琴和合成器，女声"
```

局部修改并查看变化：

```bash
python tools/compose_prompt.py \
  --text "适合学习的中文民谣，木吉他，72 BPM" \
  --set '{"bpm": 82, "mood": "warm, focused"}'
```

完整结构化输出：

```bash
python tools/compose_prompt.py --text "cinematic ambient, piano, 70 BPM" --json
```

## 数据协议 v2

唯一事实数据是 [data/prompts_v2.jsonl](data/prompts_v2.jsonl)，每行对应一条由 Pydantic 校验的 `MusicPromptV2` 记录。

```text
JSONL 事实数据
  -> 数据校验、ID 与文本去重
  -> SQLite / CSV / 网站数据 / README 统计
```

核心原则：

- `bpm_origin` 和 `key_origin` 区分 `explicit`、`inferred`、`unknown`。
- `text_quality_score` 只描述文本结构与完整度，不代表生成音乐的质量。
- `generation_score` 来自实际生成评测；没有评测时保持为空。
- `verified` 记录必须附带至少一条 `GenerationEvaluation`。
- 来源 URL、作者和许可证使用独立字段保存。

旧版 SQLite 数据可迁移：

```bash
python tools/migrate_v2.py --db data/musicprompts.db --output data/prompts_v2.jsonl
```

迁移器只补提取原文明确写出的 BPM 和调性，不使用风格猜测填充缺失参数。

## 下载与浏览

- [全部 Prompt CSV](data/final_output/csv/all_prompts.csv)
- [文本质量分 8 分以上 CSV](data/final_output/csv/curated_prompts.csv)
- [按流派浏览](prompts/genres/)
- [按场景浏览](prompts/use_cases/)
- [精校合集](prompts/curated/)

旧 Markdown 分类页保留用于阅读；新增数据应先进入 JSONL，再运行统一构建，避免多份产物各自漂移。

## 项目结构

```text
MUSICprompt/
├── data/prompts_v2.jsonl       # 可审查、可版本化的事实数据
├── src/models/v2.py           # v2 数据协议与来源标记
├── src/composer.py            # 需求解析、编译、Remix 与 Diff
├── src/repository.py          # JSONL 读写、校验和统计
├── src/db/models.py           # SQLite / FTS5 检索
├── tools/build.py             # 统一构建入口
├── tools/migrate_v2.py        # v1 -> v2 迁移
├── tools/compose_prompt.py    # Prompt 生成 CLI
├── web/                       # 无后端检索网站
└── tests/                     # 单元测试与回归测试
```

## 评测约定

实际生成评测应记录平台、模型版本、结果链接和评分。推荐维度包括风格符合度、结构符合度、人声符合度、音质和人工偏好。文本评分较高的记录不能自动标记为“生成已验证”。

## 贡献与许可证

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。代码采用 [MIT License](LICENSE)；第三方 Prompt 数据仍应保留原始来源及适用的数据许可信息。
