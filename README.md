# 🎵 MUSICprompt - AI Music Prompt Library

<p align="center">
  <img src="https://img.shields.io/badge/Total%20Prompts-283-blue?style=for-the-badge&logo=music&logoColor=white" alt="Total Prompts">
  <img src="https://img.shields.io/badge/Curated-95-gold?style=for-the-badge&logo=star&logoColor=white" alt="Curated">
  <img src="https://img.shields.io/badge/Top%20Genre-Rock-red?style=for-the-badge&logo=fire&logoColor=white" alt="Top Genre">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-brightgreen?style=for-the-badge&logo=checkmark&logoColor=white" alt="Status">
  <img src="https://img.shields.io/badge/License-MIT-blue?style=for-the-badge" alt="License">
</p>

---

## 🎯 What Problem Does This Solve? / 解决了什么技术难题？

### English

MUSICprompt solves two critical challenges in AI music generation:

1. **Automated Daily Updates**: Automatically collects and processes high-quality prompts from global communities, using Qwen2.5-72B LLM for professional translation - no more manual searching and translating.

2. **Machine Translation Quality Issues**: Traditional machine translation often distorts music terminology and loses emotional nuance. Our LLM-powered translation preserves technical accuracy (BPM, key signatures, instrument names) while maintaining creative expression.

### 中文

MUSICprompt 解决了 AI 音乐生成领域的两大核心难题：

1. **自动化每日更新**：自动从全球社区采集和处理高质量提示词，使用 Qwen2.5-72B 大模型进行专业翻译 —— 不再需要手动搜索和翻译。

2. **机翻文本失真问题**：传统机器翻译经常扭曲音乐术语，丢失情感细微差别。我们的大模型翻译保留了技术准确性（BPM、调号、乐器名称），同时保持创意表达。

---

## 🚀 Quick Start / 快速开始

### Where to Use / 在哪里使用

**GitHub Repository**: [https://github.com/Erichestein0702/MUSICprompt](https://github.com/Erichestein0702/MUSICprompt)

### How to Download / 如何下载

#### Option 1: Clone the Repository / 方式一：克隆仓库

```bash
git clone https://github.com/Erichestein0702/MUSICprompt.git
```

#### Option 2: Download CSV Files / 方式二：下载 CSV 文件

Navigate to `data/final_output/csv/` for Excel-compatible format:

| File | Description | 文件说明 |
|------|-------------|----------|
| [all_prompts.csv](data/final_output/csv/all_prompts.csv) | All 283 prompts | 全部 283 条提示词 |
| [curated_prompts.csv](data/final_output/csv/curated_prompts.csv) | 95 curated prompts (8+ score) | 95 条精校提示词（8分以上） |

#### Option 3: Browse Online / 方式三：在线浏览

- **Curated Collection**: [data/final_output/curated/](data/final_output/curated/)
- **By Genre**: [data/final_output/genres/](data/final_output/genres/)
- **By Use Case**: [data/final_output/use_cases/](data/final_output/use_cases/)

---

## 📊 Genre Distribution / 流派分布

| Genre | Count | Distribution | 流派 | 数量 |
|-------|-------|--------------|------|------|
| 🎸 **Pop** | 131 | `████████████████████▒▒▒▒` | 流行 | 131 |
| 🎸 **Rock** | 118 | `██████████████████▒▒▒▒▒▒` | 摇滚 | 118 |
| 🎹 **Electronic** | 90 | `██████████████▒▒▒▒▒▒▒▒▒` | 电子 | 90 |
| 🎤 **Soul** | 32 | `█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒` | 灵魂 | 32 |
| 🎤 **Rap** | 32 | `█████▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒` | 说唱 | 32 |

<details>
<summary>📊 Full Genre Distribution / 完整流派分布</summary>

| Genre | Count | Genre | Count |
|-------|-------|-------|-------|
| Funk | 27 | R&B | 25 |
| House | 24 | Jazz | 22 |
| Ambient | 18 | Indie | 18 |
| Blues | 16 | EDM | 15 |
| Trap | 13 | Trance | 12 |
| Hip Hop | 11 | Metal | 32 |
| Punk | 9 | Techno | 5 |

</details>

---

## ⭐ Hall of Fame / 名人堂

### 🥇 The House Of The Rising Sun

<p align="left">
  <img src="https://img.shields.io/badge/Score-9.17%2F10-gold?style=flat-square" alt="Score">
  <img src="https://img.shields.io/badge/Genre-Country%20%7C%20House-brown?style=flat-square" alt="Genre">
</p>

> **EN**: Deep vocals, mournful harmonica, steel-string guitar tremolo accompaniment — a dark country revival of the classic.
> 
> **中文**: 低沉的嗓音，悲凉的口琴，钢弦吉他的颤音伴奏 —— 黑暗乡村版的经典重生。

[View Details / 查看详情](data/final_output/curated/country_curated.md)

---

### 🥈 Burdens

<p align="left">
  <img src="https://img.shields.io/badge/Score-8.33%2F10-silver?style=flat-square" alt="Score">
  <img src="https://img.shields.io/badge/Genre-Rock%20%7C%20Electronic%20%7C%20House-red?style=flat-square" alt="Genre">
</p>

> **EN**: Portishead's melancholic Trip-Hop + Johnny Marr's complex guitar + Underworld's electronic Prog-House = an unforgettable emotional fusion.
> 
> **中文**: Portishead的忧郁Trip-Hop + Johnny Marr的复杂吉他 + Underworld的电子Prog-House = 令人难忘的情感融合。

[View Details / 查看详情](data/final_output/curated/rock_curated.md)

---

### 🥉 Shadows to Light

<p align="left">
  <img src="https://img.shields.io/badge/Score-8.17%2F10-cd7f32?style=flat-square" alt="Score">
  <img src="https://img.shields.io/badge/Genre-Rock%20%7C%20Ambient-orange?style=flat-square" alt="Genre">
</p>

> **EN**: Alternative rock/emo rock: finding hope in darkness, a healing sound of overcoming adversity.
> 
> **中文**: 另类摇滚/情绪摇滚：在黑暗中寻找希望，战胜逆境的治愈之声。

[View Details / 查看详情](data/final_output/curated/rock_curated.md)

---

## 🗂️ Navigation / 导航

### Browse by Genre / 按流派浏览

#### 🎸 Rock / 摇滚 (495 prompts)
| Sub-Genre | Count | Link | 子流派 | 数量 |
|-----------|-------|------|--------|------|
| **All Rock** | 495 | [View / 查看](data/final_output/genres/rock/rock.md) | 全部摇滚 | 495 |
| Metal | 34 | [View / 查看](data/final_output/genres/rock/metal/metal.md) | 金属 | 34 |
| Punk | 8 | [View / 查看](data/final_output/genres/rock/punk/punk.md) | 朋克 | 8 |
| Indie | 1 | [View / 查看](data/final_output/genres/rock/indie/indie.md) | 独立 | 1 |

#### 🎹 Electronic / 电子 (115 prompts)
| Sub-Genre | Count | Link | 子流派 | 数量 |
|-----------|-------|------|--------|------|
| **All Electronic** | 115 | [View / 查看](data/final_output/genres/electronic/electronic.md) | 全部电子 | 115 |
| House | 12 | [View / 查看](data/final_output/genres/electronic/house/house.md) | 浩室 | 12 |
| Trance | 10 | [View / 查看](data/final_output/genres/electronic/trance/trance.md) | 迷幻舞曲 | 10 |
| Ambient | 14 | [View / 查看](data/final_output/genres/electronic/ambient/ambient.md) | 氛围 | 14 |
| Techno | 1 | [View / 查看](data/final_output/genres/electronic/techno/techno.md) | 铁克诺 | 1 |
| Lo-fi | 2 | [View / 查看](data/final_output/genres/electronic/lo-fi/lo-fi.md) | 低保真 | 2 |

#### 🎤 Hip-Hop / 嘻哈 (97 prompts)
| Sub-Genre | Count | Link | 子流派 | 数量 |
|-----------|-------|------|--------|------|
| **All Hip-Hop** | 97 | [View / 查看](data/final_output/genres/hip-hop/hip-hop.md) | 全部嘻哈 | 97 |
| Rap | 70 | [View / 查看](data/final_output/genres/hip-hop/rap/rap.md) | 说唱 | 70 |

#### 🎵 Standalone Genres / 独立流派
| Genre | Count | Link | 流派 | 数量 |
|-------|-------|------|------|------|
| 🎤 **Pop** | 389 | [View / 查看](data/final_output/genres/pop/pop.md) | 流行 | 389 |
| 🎷 **Jazz** | 37 | [View / 查看](data/final_output/genres/jazz/jazz.md) | 爵士 | 37 |
| 🎻 **Classical** | 10 | [View / 查看](data/final_output/genres/classical/classical.md) | 古典 | 10 |
| 🪕 **Folk** | 11 | [View / 查看](data/final_output/genres/folk/folk.md) | 民谣 | 11 |
| 🤠 **Country** | 5 | [View / 查看](data/final_output/genres/country/country.md) | 乡村 | 5 |
| 🎺 **Soul** | 16 | [View / 查看](data/final_output/genres/soul/soul.md) | 灵魂 | 16 |
| 🎶 **R&B** | 20 | [View / 查看](data/final_output/genres/r&b/r&b.md) | 节奏布鲁斯 | 20 |
| 🎸 **Funk** | 16 | [View / 查看](data/final_output/genres/funk/funk.md) | 放克 | 16 |
| 🎵 **Blues** | 9 | [View / 查看](data/final_output/genres/blues/blues.md) | 布鲁斯 | 9 |
| 📁 **Else** | 71 | [View / 查看](data/final_output/genres/else/uncategorized.md) | 其他 | 71 |

### Browse by Use Case / 按场景浏览

| Use Case | Count | Link | 使用场景 | 数量 |
|----------|-------|------|----------|------|
| 🎉 **Party** | 79 | [View / 查看](data/final_output/use_cases/party.md) | 派对聚会 | 79 |
| 📚 **Study** | 35 | [View / 查看](data/final_output/use_cases/study.md) | 学习专注 | 35 |
| 🎮 **Gaming** | 18 | [View / 查看](data/final_output/use_cases/gaming.md) | 游戏电竞 | 18 |
| 🎬 **Cinematic** | 54 | [View / 查看](data/final_output/use_cases/cinematic.md) | 影视配乐 | 54 |

---

## 📈 Statistics / 数据统计

<p align="center">
  <img src="https://img.shields.io/badge/Total%20Prompts-283-blue?style=flat-square" alt="Total">
  <img src="https://img.shields.io/badge/Curated-95-gold?style=flat-square" alt="Curated">
  <img src="https://img.shields.io/badge/Parent%20Genres-13-purple?style=flat-square" alt="Parent Genres">
  <img src="https://img.shields.io/badge/Sub%20Genres-10-green?style=flat-square" alt="Sub Genres">
</p>

| Metric | Value | 指标 | 数值 |
|--------|-------|------|------|
| 🎯 Total Prompts | 283 | 总提示词 | 283 |
| ⭐ High Quality (≥7) | 283 | 高质量 (≥7分) | 283 |
| 🏆 Curated (≥8) | 95 | 精校 (≥8分) | 95 |
| 🎵 Parent Genres | 13 | 父级流派 | 13 |
| 🎶 Sub Genres | 10 | 子流派 | 10 |
| 📁 Use Cases | 8 | 使用场景 | 8 |

---

## 🛠️ Project Structure / 项目结构

```
MUSICprompt/
├── 📁 data/
│   ├── 📁 final_output/          # Final output / 最终输出
│   │   ├── ⭐ curated/            # Curated prompts / 精校合集
│   │   ├── 🎵 genres/             # By genre / 按流派分类
│   │   ├── 🎯 use_cases/          # By use case / 按场景分类
│   │   └── 📊 csv/                # CSV exports / CSV导出
│   ├── 📁 processed/              # Processed data / 处理后数据
│   └── 📁 external/               # External sources / 外部数据源
├── 📁 tools/
│   ├── 🔧 prompt_extractor.py     # Extract prompts / 提取器
│   ├── 🌐 prompt_translator.py    # AI translator / AI翻译器
│   ├── ✨ prompt_refiner.py       # Refine prompts / 精校器
│   ├── 📊 output_formatter.py     # Format output / 格式化器
│   └── 🚀 publish_update.py       # Auto publish / 自动发布
├── 📄 README.md                   # This file / 本文件
├── 📄 CONTRIBUTING.md             # Contribution guide / 贡献指南
├── 📄 LICENSE                     # MIT License / MIT许可证
└── 📄 ARCHITECTURE.md             # Architecture doc / 架构文档
```

---

## 📝 Quality Scoring System / 质量评分体系

Each prompt is evaluated on 5 dimensions / 每条提示词都经过5维度评估：

| Dimension | Weight | 维度 | 权重 |
|-----------|--------|------|------|
| 🔧 Technical Parameters | 25% | 技术参数 | 25% |
| 🏗️ Structure Clarity | 20% | 结构清晰度 | 20% |
| 🎵 Genre Specificity | 20% | 流派明确度 | 20% |
| 🎸 Instrument Precision | 20% | 乐器精确度 | 20% |
| 📏 Length Appropriateness | 15% | 长度适当性 | 15% |

---

## 🤝 Contributing / 贡献指南

We welcome contributions, especially **Phonk** and **Electronic** prompts!

我们欢迎贡献，特别是 **Phonk** 和 **Electronic** 流派的提示词！

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

详情请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## 📜 Data Sources / 数据来源

- [mister-magpie/aims_prompts](https://github.com/mister-magpie/aims_prompts) - Suno & Udio user data
- [daveshap/suno](https://github.com/daveshap/suno) - Suno AI syntax guide
- [naqashmunir21/awesome-suno-prompts](https://github.com/naqashmunir21/awesome-suno-prompts) - Community prompts

---

## 📄 License / 许可证

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE)。

---

<p align="center">
  <em>Made with 🎵 by MUSICprompt Team</em><br>
  <em>让每个人都能创作专业级AI音乐</em><br>
  <em>Empowering everyone to create professional AI music</em>
</p>
