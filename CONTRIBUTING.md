# Contributing to MUSICprompt

欢迎提交 Prompt、生成评测、数据修复和代码改进。v2 的核心要求是：**来源可追踪、参数不冒充事实、效果评分有生成记录支撑。**

## 提交 Prompt

1. Fork 仓库并创建功能分支。
2. 在 `data/prompts_v2.jsonl` 中每条记录占一行，字段由 `src/models/v2.py` 定义。
3. 运行 `python tools/build.py --check` 验证数据、去重和主要文档链接。
4. 运行 `python tools/build.py` 更新 CSV、网站数据和统计产物。
5. 运行 `python -m unittest discover -s tests -v`，然后提交 PR。

最小示例：

```json
{"schema_version":"2.0.0","id":"mp_community_example_001","title":"Midnight Circuit","style_prompt":"drift phonk, 140 BPM, F minor, cowbell, distorted 808 bass, no vocals","target_platform":"suno","genres":["phonk","electronic"],"instruments":["cowbell","808 bass"],"bpm":140,"bpm_origin":"explicit","key_signature":"F minor","key_origin":"explicit","source":{"name":"community","author":"your-github-name","license":"CC0-1.0"}}
```

### 数据规则

| 字段 | 要求 |
|---|---|
| `id` | 唯一且稳定，不要在后续编辑中随意改变 |
| `style_prompt` | 保留原始文本，不为了“看起来更专业”而覆盖原意 |
| `bpm_origin` / `key_origin` | 原文明确写出用 `explicit`；模型推测用 `inferred`；没有值用 `unknown` |
| `text_quality_score` | 只表示文本结构和完整度，不代表音乐效果 |
| `source` | 尽可能提供名称、URL、作者和许可证 |
| `evaluations` | 保存真实生成平台、模型版本、结果链接和评分 |

不要把 AI 推断的 BPM、调性或乐器写成原始 Prompt 明确提供的参数。不要仅凭文本评分把记录标记为 `verified`。

## 提交生成评测

`GenerationEvaluation` 支持以下信息：

- 平台与模型版本
- 音频或结果页面 URL
- 0–10 分的 `generation_score`
- 风格、结构、人声、音质等分项评分
- 失败原因或人工评价

一条记录可以保留多次生成结果，用于比较 Prompt 修改前后的表现。

## 提交代码

- 新功能应包含标准库 `unittest` 测试，不依赖真实 API 或外部网络。
- 不提交 `.env`、API Key 或本地凭据。
- SQLite 是构建产物；可审查的数据修改应落在 JSONL。
- 自动采集规则变更应同时补充正例和反例测试。

## 行为准则

尊重贡献者，讨论具体问题和证据。涉及第三方数据时，不要移除来源、作者或许可证信息。
