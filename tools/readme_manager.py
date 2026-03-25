#!/usr/bin/env python
"""
VMDP README 管理器 - 自动情报看板生成器

该脚本扫描 data/genres/ 下的 JSON 数据，自动更新根目录的 README.md，
生成动态情报看板、爆款预览、技术特征云等内容。

使用占位符逻辑，只替换指定区域，保护手动修改的内容。

Usage:
    python tools/readme_manager.py [--dry-run]
"""

import argparse
import json
import logging
import os
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core import setup_secure_logging
from src.models import MusicGenre, GENRE_DISPLAY_NAMES


GENRES_DIR = PROJECT_ROOT / "data" / "genres"
README_FILE = PROJECT_ROOT / "README.md"

PLACEHOLDER_START = "<!-- VMDP_AUTO_START -->"
PLACEHOLDER_END = "<!-- VMDP_AUTO_END -->"

GENRE_ICONS = {
    "electronic": "🎧",
    "electronic.bass": "🔊",
    "electronic.bass.trap": "🔥",
    "electronic.bass.dubstep": "💥",
    "electronic.bass.hardstyle": "⚡",
    "electronic.house": "🏠",
    "electronic.trance": "✨",
    "electronic.phonk_funk": "🎸",
    "electronic.techno": "🎛️",
    "electronic.else": "💿",
    "hip_hop": "🎤",
    "hip_hop.trap": "🎯",
    "hip_hop.boombap": "🥁",
    "cinematic": "🎬",
    "pop": "🎵",
    "rock": "🎸",
    "ambient": "🌙",
    "classical": "🎻",
    "jazz": "🎷",
    "rnb": "💜",
    "lo_fi": "📻",
    "folk": "🪕",
    "world": "🌍",
    "experimental": "🧪",
    "other": "📦",
}


class ReadmeManager:
    """
    README 管理器 - 自动生成情报看板
    
    功能：
    1. 数据聚合：扫描 data/genres/ 下的所有 JSON 文件
    2. 动态看板：生成情报概览表格
    3. 爆款预览：展示热门流派的双语 Prompt
    4. 技术特征云：提取高频 DSP 关键词
    5. 占位符保护：只替换指定区域，保护手动修改
    """
    
    def __init__(self, dry_run: bool = False):
        """
        初始化 README 管理器
        
        Args:
            dry_run: 是否为试运行模式（不写入文件）
        """
        self.dry_run = dry_run
        self.logger = logging.getLogger("ReadmeManager")
        
        self.genre_data: Dict[str, Dict[str, Any]] = {}
        self.all_documents: List[Dict[str, Any]] = []
        self.genre_stats: Dict[str, Dict[str, Any]] = {}
    
    def scan_genres(self) -> Dict[str, Dict[str, Any]]:
        """
        扫描 data/genres/ 下的所有 JSON 文件
        
        Returns:
            流派数据字典
        """
        if not GENRES_DIR.exists():
            self.logger.warning(f"流派目录不存在: {GENRES_DIR}")
            return {}
        
        for genre_file in GENRES_DIR.rglob("*.json"):
            try:
                with open(genre_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                genre = data.get("genre", genre_file.stem)
                self.genre_data[genre] = data
                
                documents = data.get("documents", [])
                self.all_documents.extend(documents)
                
                self.logger.info(f"加载流派: {genre} ({len(documents)} 条)")
                
            except Exception as e:
                self.logger.error(f"读取文件失败 {genre_file}: {e}")
        
        self.logger.info(f"共加载 {len(self.genre_data)} 个流派，{len(self.all_documents)} 条文档")
        return self.genre_data
    
    def calculate_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        计算各流派统计信息
        
        Returns:
            统计信息字典
        """
        for genre, data in self.genre_data.items():
            documents = data.get("documents", [])
            count = len(documents)
            
            if count > 0:
                avg_viral = sum(d.get("viral_score", 0) for d in documents) / count
                updated_at = data.get("updated_at", datetime.now().isoformat())
            else:
                avg_viral = 0
                updated_at = datetime.now().isoformat()
            
            self.genre_stats[genre] = {
                "count": count,
                "avg_viral_score": round(avg_viral, 1),
                "updated_at": updated_at,
                "icon": GENRE_ICONS.get(genre, "🎵"),
                "display_name": GENRE_DISPLAY_NAMES.get(genre, genre),
            }
        
        return self.genre_stats
    
    def generate_overview_table(self) -> str:
        """
        生成情报概览表格
        
        Returns:
            Markdown 表格字符串
        """
        if not self.genre_stats:
            return "*暂无数据*"
        
        sorted_genres = sorted(
            self.genre_stats.items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )
        
        lines = [
            "| 图标 | 流派 | 收录数量 | 平均爆款指数 | 最后更新 |",
            "|:---:|------|:-------:|:-----------:|----------|",
        ]
        
        for genre, stats in sorted_genres:
            if stats["count"] == 0:
                continue
            
            icon = stats["icon"]
            name = stats["display_name"]
            count = stats["count"]
            avg_viral = stats["avg_viral_score"]
            
            try:
                dt = datetime.fromisoformat(stats["updated_at"].replace("Z", "+00:00"))
                updated = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                updated = stats["updated_at"][:16]
            
            lines.append(f"| {icon} | {name} | {count} | {avg_viral}% | {updated} |")
        
        return "\n".join(lines)
    
    def generate_hot_preview(
        self,
        target_genres: List[str],
        count: int = 3
    ) -> str:
        """
        生成爆款预览
        
        Args:
            target_genres: 目标流派列表
            count: 每个流派展示的数量
            
        Returns:
            Markdown 内容
        """
        sections = []
        
        for genre in target_genres:
            genre_docs = []
            
            for g, data in self.genre_data.items():
                if g == genre or g.startswith(genre + "."):
                    genre_docs.extend(data.get("documents", []))
            
            if not genre_docs:
                continue
            
            sorted_docs = sorted(
                genre_docs,
                key=lambda x: x.get("viral_score", 0),
                reverse=True
            )[:count]
            
            icon = GENRE_ICONS.get(genre, "🎵")
            display_name = GENRE_DISPLAY_NAMES.get(genre, genre)
            
            section_lines = [
                f"### {icon} {display_name} 爆款预览",
                "",
            ]
            
            for i, doc in enumerate(sorted_docs, 1):
                title = doc.get("title", {})
                title_zh = title.get("zh", "未知标题") if isinstance(title, dict) else str(title)
                title_en = title.get("en", "Unknown") if isinstance(title, dict) else str(title)
                
                prompt = doc.get("prompt", {})
                prompt_zh = prompt.get("zh", "") if isinstance(prompt, dict) else ""
                prompt_en = prompt.get("en", "") if isinstance(prompt, dict) else ""
                
                viral_score = doc.get("viral_score", 0)
                
                section_lines.extend([
                    f"#### {i}. {title_zh}",
                    f"> **爆款指数**: {viral_score}%",
                    ">",
                    f"> **中文**: {prompt_zh[:100]}{'...' if len(prompt_zh) > 100 else ''}",
                    ">",
                    f"> **English**: {prompt_en[:100]}{'...' if len(prompt_en) > 100 else ''}",
                    "",
                ])
            
            sections.append("\n".join(section_lines))
        
        return "\n\n".join(sections)
    
    def extract_tech_keywords(self) -> Dict[str, int]:
        """
        从 dsp_params 中提取高频技术关键词
        
        Returns:
            关键词频率字典
        """
        keywords = Counter()
        
        tech_patterns = [
            r"(\d+Hz)",
            r"(sidechain)",
            r"(compression)",
            r"(reverb)",
            r"(boost)",
            r"(cut)",
            r"(eq)",
            r"(bass)",
            r"(sub)",
            r"(high|mid|low)",
            r"(attack)",
            r"(release)",
            r"(saturation)",
            r"(distortion)",
            r"(stereo)",
            r"(mono)",
            r"(parallel)",
            r"(multiband)",
            r"(limiter)",
            r"(compressor)",
        ]
        
        for doc in self.all_documents:
            dsp_params = doc.get("dsp_params", {})
            gem_suggestion = doc.get("gem_suggestion", "").lower()
            
            for key, value in dsp_params.items():
                if value:
                    text = str(value).lower()
                    for pattern in tech_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            keywords[match.title()] += 1
            
            for pattern in tech_patterns:
                matches = re.findall(pattern, gem_suggestion, re.IGNORECASE)
                for match in matches:
                    keywords[match.title()] += 1
        
        return dict(keywords.most_common(20))
    
    def generate_tech_cloud(self) -> str:
        """
        生成技术特征云
        
        Returns:
            Markdown 内容
        """
        keywords = self.extract_tech_keywords()
        
        if not keywords:
            return "*暂无技术特征数据*"
        
        max_count = max(keywords.values())
        
        cloud_items = []
        for keyword, count in keywords.items():
            if max_count > 0:
                size = 1 + (count / max_count) * 2
            else:
                size = 1
            
            font_size = int(12 + size * 6)
            opacity = 0.5 + (count / max_count) * 0.5 if max_count > 0 else 0.5
            
            cloud_items.append(
                f'<span style="font-size: {font_size}px; opacity: {opacity:.2f}">{keyword}</span>'
            )
        
        return " ".join(cloud_items)
    
    def generate_summary_stats(self) -> str:
        """
        生成总体统计摘要
        
        Returns:
            Markdown 内容
        """
        total_docs = len(self.all_documents)
        total_genres = len([g for g, s in self.genre_stats.items() if s["count"] > 0])
        
        if total_docs > 0:
            avg_viral = sum(d.get("viral_score", 0) for d in self.all_documents) / total_docs
            max_viral = max(d.get("viral_score", 0) for d in self.all_documents)
        else:
            avg_viral = 0
            max_viral = 0
        
        return f"""
| 指标 | 数值 |
|------|------|
| 📊 总收录 Prompt | **{total_docs}** 条 |
| 🎵 覆盖流派 | **{total_genres}** 个 |
| 📈 平均爆款指数 | **{avg_viral:.1f}%** |
| 🔥 最高爆款指数 | **{max_viral:.1f}%** |
"""
    
    def generate_auto_content(self) -> str:
        """
        生成完整的自动内容
        
        Returns:
            Markdown 内容
        """
        self.scan_genres()
        self.calculate_stats()
        
        overview_table = self.generate_overview_table()
        hot_preview = self.generate_hot_preview(
            target_genres=["electronic.phonk_funk", "electronic.bass"],
            count=3
        )
        tech_cloud = self.generate_tech_cloud()
        summary_stats = self.generate_summary_stats()
        
        content = f"""
{PLACEHOLDER_START}

> 🤖 **本区域由 VMDP 自动生成，请勿手动修改**
> 
> 最后更新时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 情报概览

{summary_stats}

---

## 🎵 流派分布

{overview_table}

---

## 🔥 爆款预览

{hot_preview}

---

## 🛠️ 技术特征云

{tech_cloud}

---

{PLACEHOLDER_END}
"""
        return content
    
    def update_readme(self) -> bool:
        """
        更新 README.md
        
        使用占位符逻辑，只替换指定区域，保护手动修改的内容。
        
        Returns:
            是否成功更新
        """
        auto_content = self.generate_auto_content()
        
        if not README_FILE.exists():
            self.logger.info("README.md 不存在，创建新文件")
            full_content = self._create_new_readme(auto_content)
        else:
            with open(README_FILE, 'r', encoding='utf-8') as f:
                existing_content = f.read()
            
            if PLACEHOLDER_START in existing_content and PLACEHOLDER_END in existing_content:
                pattern = re.escape(PLACEHOLDER_START) + r".*?" + re.escape(PLACEHOLDER_END)
                full_content = re.sub(
                    pattern,
                    auto_content.strip(),
                    existing_content,
                    flags=re.DOTALL
                )
                self.logger.info("已更新占位符区域")
            else:
                self.logger.info("未找到占位符，在文件末尾追加内容")
                full_content = existing_content.rstrip() + "\n\n" + auto_content
        
        if self.dry_run:
            self.logger.info("试运行模式，不写入文件")
            print("\n" + "=" * 60)
            print("生成的 README 内容预览")
            print("=" * 60)
            print(full_content[:2000])
            if len(full_content) > 2000:
                print("\n... (内容过长，已截断)")
            return True
        
        with open(README_FILE, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        self.logger.info(f"README.md 已更新: {README_FILE}")
        return True
    
    def _create_new_readme(self, auto_content: str) -> str:
        """
        创建新的 README.md
        
        Args:
            auto_content: 自动生成的内容
            
        Returns:
            完整的 README 内容
        """
        return f"""# VMDP - 海外音频情报中转站

> ⚠️ **免责声明**
> 
> 本项目数据源自 Reddit 社区公开内容，仅供学习研究使用，**禁止商用**。
> 所有内容的版权归原作者所有。如需删除某条内容，请提交 Issue。

---

## 📖 项目简介

VMDP（Viral Music DNA Protocol）是一个自动化音乐 Prompt 情报中转站，
从海外社区采集优质 Prompt，经过 AI 炼金处理后，输出标准化的双语数据。

### 核心功能

- 🎯 **智能采集**：自动抓取 Reddit 热门 Prompt
- 🌐 **双语翻译**：中英文对照，降低理解门槛
- 🎛️ **DSP 增强**：AI 自动补充专业音频参数
- 📊 **爆款指数**：量化评估 Prompt 潜力
- 🏷️ **本土化标签**：抖音热门标签对齐

---

## 🚀 快速开始

```bash
# 安装依赖
pip install -e .[dev]

# 运行冷启动脚本
python tools/cold_start_alchemist.py --create-sample
python tools/cold_start_alchemist.py

# 更新 README
python tools/readme_manager.py
```

---

{auto_content}

---

## 📁 项目结构

```
vmdp-pipeline/
├── src/
│   ├── core/           # 核心模块（安全、LLM、提供者）
│   └── models/         # 数据模型
├── tools/
│   ├── cold_start_alchemist.py  # 冷启动脚本
│   └── readme_manager.py        # README 管理器
├── data/
│   ├── genres/         # 按流派分类的数据
│   ├── raw/            # 原始 Prompt
│   └── processed/      # 处理状态
└── README.md
```

---

## 📄 许可证

本项目仅供学习研究使用，禁止商用。
"""


def main():
    parser = argparse.ArgumentParser(
        description="VMDP README 管理器 - 自动情报看板生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行模式，不写入文件'
    )
    
    args = parser.parse_args()
    
    setup_secure_logging(
        level=logging.INFO,
        log_format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    logger = logging.getLogger("main")
    logger.info("VMDP README 管理器启动")
    
    try:
        manager = ReadmeManager(dry_run=args.dry_run)
        success = manager.update_readme()
        
        if success:
            logger.info("README 更新完成")
        else:
            logger.error("README 更新失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
