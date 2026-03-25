# Contributing to MUSICprompt / 贡献指南

[English](#english) | [中文](#中文)

---

## English

### 🎵 Thank You for Contributing!

MUSICprompt is a community-driven project. We welcome contributions of high-quality AI music prompts, especially in **Phonk** and **Electronic** genres.

### How to Contribute

#### 1. Fork the Repository

Click the "Fork" button on the top right of this page to create your own copy.

#### 2. Clone Your Fork

```bash
git clone https://github.com/YOUR_USERNAME/MUSICprompt.git
cd MUSICprompt
```

#### 3. Create a Branch

```bash
git checkout -b feature/add-new-prompts
```

#### 4. Add Your Prompts

Create a new JSON file in `data/contributions/` folder:

```json
[
  {
    "prompt_text": "Your prompt with [Verse], [Chorus] tags",
    "genre": ["phonk", "electronic"],
    "bpm": 140,
    "key": "F Minor",
    "instruments": ["808 bass", "cowbell", "synth"],
    "description": "Brief style description",
    "contributor": "Your GitHub username"
  }
]
```

**Prompt Quality Guidelines:**

| Requirement | Description |
|-------------|-------------|
| **Length** | 50-950 characters |
| **Structure** | Use `[Verse]`, `[Chorus]`, `[Bridge]` tags |
| **BPM** | Include specific tempo (e.g., 140 BPM) |
| **Key** | Specify key signature (e.g., F Minor) |
| **Instruments** | List specific instruments |
| **Style** | Describe the genre clearly |

#### 5. Test Your Prompts

Before submitting, test your prompts on:
- [Suno AI](https://suno.ai)
- [Udio](https://udio.com)

#### 6. Commit and Push

```bash
git add .
git commit -m "feat: add new Phonk prompts"
git push origin feature/add-new-prompts
```

#### 7. Create Pull Request

1. Go to your fork on GitHub
2. Click "Compare & pull request"
3. Fill in the PR template
4. Submit!

### What We're Looking For

| Genre | Priority | Examples |
|-------|----------|----------|
| **Phonk** | 🔥 High | Drift Phonk, Aggressive Phonk, Memphis Phonk |
| **Electronic** | 🔥 High | House, Trance, Dubstep, Future Bass |
| **Brazilian Funk** | ⭐ Medium | Funk Carioca, Brega Funk |
| **Hip-Hop/Trap** | ⭐ Medium | Trap, Drill, Lo-fi Hip Hop |

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community

---

## 中文

### 🎵 感谢您的贡献！

MUSICprompt 是一个社区驱动的项目。我们欢迎高质量 AI 音乐提示词的贡献，特别是 **Phonk** 和 **Electronic** 流派。

### 如何贡献

#### 1. Fork 仓库

点击页面右上角的 "Fork" 按钮创建你自己的副本。

#### 2. 克隆你的 Fork

```bash
git clone https://github.com/YOUR_USERNAME/MUSICprompt.git
cd MUSICprompt
```

#### 3. 创建分支

```bash
git checkout -b feature/add-new-prompts
```

#### 4. 添加你的提示词

在 `data/contributions/` 文件夹中创建新的 JSON 文件：

```json
[
  {
    "prompt_text": "你的提示词，包含 [Verse], [Chorus] 标签",
    "genre": ["phonk", "electronic"],
    "bpm": 140,
    "key": "F Minor",
    "instruments": ["808 bass", "cowbell", "synth"],
    "description": "风格简述",
    "contributor": "你的 GitHub 用户名"
  }
]
```

**提示词质量指南：**

| 要求 | 描述 |
|------|------|
| **长度** | 50-950 字符 |
| **结构** | 使用 `[Verse]`, `[Chorus]`, `[Bridge]` 标签 |
| **BPM** | 包含具体速度（如 140 BPM） |
| **调性** | 指定调号（如 F Minor） |
| **乐器** | 列出具体乐器 |
| **风格** | 清晰描述流派 |

#### 5. 测试你的提示词

提交前，请在以下平台测试：
- [Suno AI](https://suno.ai)
- [Udio](https://udio.com)

#### 6. 提交并推送

```bash
git add .
git commit -m "feat: 添加新的 Phonk 提示词"
git push origin feature/add-new-prompts
```

#### 7. 创建 Pull Request

1. 在 GitHub 上进入你的 fork
2. 点击 "Compare & pull request"
3. 填写 PR 模板
4. 提交！

### 我们正在寻找的内容

| 流派 | 优先级 | 示例 |
|------|--------|------|
| **Phonk** | 🔥 高 | Drift Phonk, Aggressive Phonk, Memphis Phonk |
| **Electronic** | 🔥 高 | House, Trance, Dubstep, Future Bass |
| **Brazilian Funk** | ⭐ 中 | Funk Carioca, Brega Funk |
| **Hip-Hop/Trap** | ⭐ 中 | Trap, Drill, Lo-fi Hip Hop |

### 行为准则

- 保持尊重和包容
- 提供建设性反馈
- 关注社区共同利益

---

## Questions? / 有问题？

- Open an [Issue](https://github.com/Erichestein0702/MUSICprompt/issues)
- Start a [Discussion](https://github.com/Erichestein0702/MUSICprompt/discussions)
