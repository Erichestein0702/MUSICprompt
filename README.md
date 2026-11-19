# MUSICprompt

面向 AI 音乐创作的开源 Prompt 数据集、检索工具与确定性 Prompt 编译器。

v2 的重点不是单纯增加文本数量，而是让数据**可审查、可迁移、可检索、可验证**：区分原始参数与模型推断，区分文本质量与实际生成效果。

## 当前数据

<!-- AUTO_STATS:START -->
| 指标 | 当前值 |
|---|---:|
| 不重复 Prompt | 283 |
| 文本质量分 ≥ 8（仅文本参考） | 95 |
| 生成效果验证通过 | 0 |
| 评测任务完成 | 0 / 40 |
| 有明确 BPM | 49 |
| 有明确调性 | 23 |
| 平均文本质量分 | 7.44 |
| 平均生成分 | 暂无 |
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
- [生成效果验证通过 CSV](data/final_output/csv/curated_prompts.csv)（由真实评测结果驱动）
- [文本质量分 8 分以上 CSV](data/final_output/csv/text_quality_prompts.csv)（仅文本参考）
- [按流派浏览](prompts/genres/)
- [按场景浏览](prompts/use_cases/)
- [精校合集](prompts/curated/)

旧 Markdown 分类页保留用于阅读；新增数据应先进入 JSONL，再运行统一构建，避免多份产物各自漂移。

## 项目结构

```text
MUSICprompt/
├── data/prompts_v2.jsonl       # 可审查、可版本化的事实数据
├── data/eval_tasks.jsonl      # 固定评测任务集（测试用例，不含结果）
├── data/eval_results.jsonl    # 真实生成评测记录（唯一评测事实源）
├── src/models/v2.py           # v2 数据协议与来源标记
├── src/models/eval.py         # 评测任务/结果模型与状态推导
├── src/composer.py            # 需求解析、编译、Remix 与 Diff
├── src/repository.py          # JSONL 读写、校验和统计
├── src/db/models.py           # SQLite / FTS5 检索
├── tools/build.py             # 统一构建入口
├── tools/eval_run.py          # 评测管理 CLI（list/record/report/apply）
├── tools/migrate_v2.py        # v1 -> v2 迁移
├── tools/compose_prompt.py    # Prompt 生成 CLI
├── web/                       # 无后端检索网站
└── tests/                     # 单元测试与回归测试
```

## 效果评测

“精选/已验证”由**真实生成效果**驱动，不由文本质量分决定。文本质量分只描述提示词文本本身的完整度。

固定评测任务集在 [data/eval_tasks.jsonl](data/eval_tasks.jsonl)，共 40 条：

- **12 条固定 Prompt 复测**：覆盖 pop、rock、electronic、rap、soul、metal、funk、r&b、house、jazz、indie、ambient。
- **28 条需求编译测试**：覆盖场景（派对/学习/睡眠/影视/游戏/冥想/健身/工作）、人声语言（中文/英文/器乐/说唱/合唱）、结构能量（build-up/三段式/drop/转调）、参数精确性（BPM/调性/乐器/拍号）与负向约束（避免 drop/炫技/autotune/失真）。

每条任务包含验收点 `expected` 与评分维度（风格还原、结构、人声、音质、音乐性）。**任务集只是测试用例设计，不含任何生成结果。**

评测流程：

```bash
# 1. 查看任务与进度
python tools/eval_run.py --list

# 2. 在生成平台（如 Suno / Udio）真实生成并试听后，录入结果
python tools/eval_run.py --record --task EV001 --platform suno \
  --model suno-v5 --audio https://example.com/demo.mp3 \
  --score 8.2 \
  --ratings '{"style_fidelity":9,"structure":8,"vocal":7,"audio_quality":8,"musicality":8}' \
  --notes "副歌还原好，bridge 略偏"

# 3. 汇总报告
python tools/eval_run.py --report

# 4. 回填到 Prompt 并刷新验证状态
python tools/eval_run.py --apply
python tools/build.py
```

验证状态推导规则：

- 无任何评测记录 → `unverified`
- 有评测但平均生成分 < 8.0 → `tested`
- 平均生成分 ≥ 8.0 → `verified`（进入精选）

**评测结果必须来自真实试听，不允许用文本分数推导或伪造音频链接与评分。** 文本评分较高的记录不能自动标记为“生成已验证”。

## 贡献与许可证

贡献方式见 [CONTRIBUTING.md](CONTRIBUTING.md)。代码采用 [MIT License](LICENSE)；第三方 Prompt 数据仍应保留原始来源及适用的数据许可信息。
