#!/usr/bin/env python
"""
MUSICprompt 全自动数据摄取与炼金流水线

该脚本实现端到端的数据处理流程：
1. 自动抓取 GitHub 仓库数据
2. 数据清洗与去重
3. 调用炼金脚本处理
4. 生成执行报告

Usage:
    python tools/auto_pipeline.py [--skip-fetch] [--skip-process] [--dry-run]
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
import hashlib

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import setup_secure_logging
from src.config import config as app_config
from src.constants import MUSIC_KEYWORDS

PROJECT_ROOT = app_config.project_root
DATA_DIR = app_config.data_dir
RAW_DIR = DATA_DIR / "raw"
EXTERNAL_DIR = app_config.output.EXTERNAL_DIR
PROCESSED_DIR = app_config.output.PROCESSED_DIR
RAW_PROMPTS_FILE = app_config.pipeline.RAW_PROMPTS_FILE


@dataclass
class SourceRepository:
    """数据源仓库配置"""
    owner: str
    repo: str
    branch: str = "main"
    target_files: List[str] = field(default_factory=list)
    description: str = ""
    
    @property
    def repo_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}.git"
    
    @property
    def clone_dir(self) -> str:
        return f"{self.owner}_{self.repo}"
    
    def raw_url(self, file_path: str) -> str:
        """获取 GitHub Raw 文件 URL"""
        return f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{self.branch}/{file_path}"


SOURCES = [
    SourceRepository(**src)
    for src in app_config.github.SOURCES
]


class DataFetcher:
    """
    数据抓取器
    
    负责从 GitHub 仓库获取数据，支持两种方式：
    1. Git 克隆（首选）
    2. HTTP 直接下载（备选）
    """
    
    def __init__(self):
        self.logger = logging.getLogger("DataFetcher")
        self.fetched_files: List[Path] = []
        self.download_dir = EXTERNAL_DIR / "downloads"
    
    def clone_repository(self, source: SourceRepository) -> Optional[Path]:
        """克隆仓库到本地"""
        clone_dir = EXTERNAL_DIR / source.clone_dir
        
        if clone_dir.exists():
            self.logger.info(f"仓库已存在，尝试更新: {source.repo}")
            try:
                subprocess.run(
                    ["git", "pull"],
                    cwd=str(clone_dir),
                    check=True,
                    capture_output=True
                )
                self.logger.info(f"仓库更新成功: {source.repo}")
            except subprocess.CalledProcessError as e:
                self.logger.warning(f"仓库更新失败，使用现有版本: {e}")
        else:
            self.logger.info(f"克隆仓库: {source.repo_url}")
            try:
                subprocess.run(
                    ["git", "clone", "--depth", "1", source.repo_url, str(clone_dir)],
                    check=True,
                    capture_output=True
                )
                self.logger.info(f"仓库克隆成功: {source.repo}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"仓库克隆失败: {e.stderr.decode() if e.stderr else str(e)}")
                return None
        
        return clone_dir
    
    def download_file_via_http(self, source: SourceRepository, file_path: str) -> Optional[Path]:
        """通过 HTTP 直接下载文件"""
        self.download_dir.mkdir(parents=True, exist_ok=True)
        
        url = source.raw_url(file_path)
        local_path = self.download_dir / f"{source.owner}_{source.repo}_{file_path.replace('/', '_')}"
        
        self.logger.info(f"尝试 HTTP 下载: {url}")
        
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode('utf-8', errors='ignore')
            
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.logger.info(f"HTTP 下载成功: {local_path.name}")
            return local_path
            
        except Exception as e:
            self.logger.warning(f"HTTP 下载失败: {e}")
            return None
    
    def fetch_via_http(self, source: SourceRepository) -> List[Path]:
        """通过 HTTP 直接下载目标文件"""
        files = []
        
        for target_file in source.target_files:
            file_path = self.download_file_via_http(source, target_file)
            if file_path:
                files.append(file_path)
        
        common_files = ["README.md", "prompts.md", "prompts.txt", "prompts.csv"]
        for file_name in common_files:
            if file_name not in source.target_files:
                file_path = self.download_file_via_http(source, file_name)
                if file_path:
                    files.append(file_path)
        
        return files
    
    def find_target_files(self, clone_dir: Path, target_patterns: List[str]) -> List[Path]:
        """在克隆目录中查找目标文件"""
        matched_files = []
        
        for pattern in target_patterns:
            for file_path in clone_dir.rglob(pattern):
                if file_path.is_file() and file_path.suffix in ['.md', '.txt', '.csv']:
                    matched_files.append(file_path)
        
        for ext in ['.md', '.txt', '.csv']:
            for file_path in clone_dir.rglob(f"*{ext}"):
                if file_path not in matched_files:
                    matched_files.append(file_path)
        
        return matched_files
    
    def fetch_source(self, source: SourceRepository) -> List[Path]:
        """抓取单个源的数据，优先 Git 克隆，失败则 HTTP 下载"""
        self.logger.info(f"处理源: {source.description}")
        
        clone_dir = self.clone_repository(source)
        
        if clone_dir:
            files = self.find_target_files(clone_dir, source.target_files)
            if files:
                self.logger.info(f"从克隆仓库找到 {len(files)} 个文件")
                return files
        
        self.logger.info("Git 克隆失败，尝试 HTTP 直接下载...")
        files = self.fetch_via_http(source)
        
        if files:
            self.logger.info(f"通过 HTTP 下载获取 {len(files)} 个文件")
        
        return files
    
    def fetch_all(self) -> List[Path]:
        """抓取所有源仓库的数据"""
        EXTERNAL_DIR.mkdir(parents=True, exist_ok=True)
        
        all_files = []
        
        for source in SOURCES:
            files = self.fetch_source(source)
            all_files.extend(files)
            self.logger.info(f"获取到 {len(files)} 个文件")
        
        self.fetched_files = all_files
        return all_files


class DataCleaner:
    """
    数据清洗器
    
    负责从原始文件中提取 Prompt 并进行去重。
    """

    def __init__(self):
        self.logger = logging.getLogger("DataCleaner")
        self.extracted_prompts: Set[str] = set()
        self.MIN_PROMPT_LENGTH = app_config.pipeline.MIN_PROMPT_LENGTH
        self.MAX_PROMPT_LENGTH = app_config.pipeline.MAX_PROMPT_LENGTH
    
    def extract_from_markdown(self, content: str) -> List[str]:
        """从 Markdown 内容中提取 Prompt"""
        prompts = []
        
        code_blocks = re.findall(r'```[^\n]*\n(.*?)```', content, re.DOTALL)
        for block in code_blocks:
            cleaned = self._clean_prompt(block)
            if cleaned:
                prompts.append(cleaned)
        
        inline_code = re.findall(r'`([^`]{10,})`', content)
        for code in inline_code:
            cleaned = self._clean_prompt(code)
            if cleaned:
                prompts.append(cleaned)
        
        bracket_items = re.findall(r'\[([^\]]+)\]', content)
        for item in bracket_items:
            if self._is_music_related(item) or len(item) >= 3:
                cleaned = self._clean_prompt(item)
                if cleaned:
                    prompts.append(cleaned)
        
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if self._is_music_related(para) and len(para) > self.MIN_PROMPT_LENGTH:
                cleaned = self._clean_prompt(para)
                if cleaned:
                    prompts.append(cleaned)
        
        return prompts
    
    def extract_from_csv(self, content: str) -> List[str]:
        """从 CSV 内容中提取 Prompt"""
        prompts = []
        lines = content.strip().split('\n')
        
        for line in lines[1:]:
            parts = line.split(',')
            for part in parts:
                cleaned = self._clean_prompt(part.strip('"'))
                if cleaned:
                    prompts.append(cleaned)
        
        return prompts
    
    def _clean_prompt(self, text: str) -> Optional[str]:
        """
        清洗 Prompt 文本
        
        特判逻辑：如果文本包含 []，则不受 20 个字符的最小长度限制
        """
        text = text.strip()
        
        text = re.sub(r'^```.*?\n', '', text)
        text = re.sub(r'\n```$', '', text)
        text = re.sub(r'[#*_`~]+', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        has_brackets = bool(re.search(r'\[.*?\]', text))
        
        if has_brackets:
            if len(text) < 3:
                return None
        else:
            if len(text) < self.MIN_PROMPT_LENGTH:
                return None
        
        if len(text) > self.MAX_PROMPT_LENGTH:
            return None
        
        if not has_brackets and not self._is_music_related(text):
            return None
        
        if text.lower().startswith(('http', 'www', 'github')):
            return None
        
        if re.match(r'^[\d\s\.,\-:;]+$', text):
            return None
        
        return text
    
    def _is_music_related(self, text: str) -> bool:
        """检查文本是否与音乐相关"""
        text_lower = text.lower()
        return any(kw in text_lower for kw in MUSIC_KEYWORDS)
    
    def process_file(self, file_path: Path) -> List[str]:
        """处理单个文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            self.logger.warning(f"读取文件失败 {file_path}: {e}")
            return []
        
        ext = file_path.suffix.lower()
        
        if ext == '.csv':
            return self.extract_from_csv(content)
        else:
            return self.extract_from_markdown(content)
    
    def process_all(self, files: List[Path]) -> Set[str]:
        """处理所有文件并去重"""
        all_prompts = []
        
        for file_path in files:
            self.logger.info(f"处理文件: {file_path.name}")
            prompts = self.process_file(file_path)
            all_prompts.extend(prompts)
            self.logger.info(f"提取到 {len(prompts)} 条 Prompt")
        
        unique_prompts = set()
        seen_hashes = set()
        
        for prompt in all_prompts:
            prompt_hash = hashlib.md5(prompt.encode()).hexdigest()
            if prompt_hash not in seen_hashes:
                seen_hashes.add(prompt_hash)
                unique_prompts.add(prompt)
        
        self.extracted_prompts = unique_prompts
        self.logger.info(f"去重后共 {len(unique_prompts)} 条唯一 Prompt")
        
        return unique_prompts
    
    def save_prompts(self, output_file: Path) -> int:
        """保存提取的 Prompt 到文件"""
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for prompt in sorted(self.extracted_prompts):
                f.write(f"{prompt}\n")
        
        self.logger.info(f"已保存 {len(self.extracted_prompts)} 条 Prompt 到 {output_file}")
        return len(self.extracted_prompts)


class PipelineRunner:
    """流水线运行器"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.logger = logging.getLogger("PipelineRunner")
        
        self.fetcher = DataFetcher()
        self.cleaner = DataCleaner()
        
        self.stats = {
            "start_time": None,
            "end_time": None,
            "files_fetched": 0,
            "prompts_extracted": 0,
            "prompts_unique": 0,
            "processing_triggered": False,
            "errors": [],
        }
    
    def run(self, skip_fetch: bool = False, skip_process: bool = False) -> Dict[str, Any]:
        """执行完整流水线"""
        self.stats["start_time"] = datetime.now().isoformat()
        
        self.logger.info("=" * 60)
        self.logger.info("MUSICprompt 全自动数据摄取与炼金流水线启动")
        self.logger.info("=" * 60)
        
        if not skip_fetch:
            self.logger.info("\n[阶段 1] 数据抓取")
            self.logger.info("-" * 40)
            
            if self.dry_run:
                self.logger.info("试运行模式，跳过实际抓取")
                self.stats["files_fetched"] = 0
            else:
                files = self.fetcher.fetch_all()
                self.stats["files_fetched"] = len(files)
                
                self.logger.info("\n[阶段 2] 数据清洗")
                self.logger.info("-" * 40)
                
                unique_prompts = self.cleaner.process_all(files)
                self.stats["prompts_extracted"] = sum(
                    len(self.cleaner.process_file(f)) for f in files
                )
                self.stats["prompts_unique"] = len(unique_prompts)
                
                if unique_prompts:
                    self.cleaner.save_prompts(RAW_PROMPTS_FILE)
        else:
            self.logger.info("跳过数据抓取阶段")
        
        if not skip_process:
            self.logger.info("\n[阶段 3] 炼金处理")
            self.logger.info("-" * 40)
            
            if self.dry_run:
                self.logger.info("试运行模式，跳过实际处理")
            else:
                self._trigger_alchemist()
        else:
            self.logger.info("跳过炼金处理阶段")
        
        self.stats["end_time"] = datetime.now().isoformat()
        
        self._generate_report()
        
        return self.stats
    
    def _trigger_alchemist(self) -> bool:
        """触发炼金脚本"""
        alchemist_script = PROJECT_ROOT / "tools" / "cold_start_alchemist.py"
        
        if not alchemist_script.exists():
            self.logger.error(f"炼金脚本不存在: {alchemist_script}")
            self.stats["errors"].append("炼金脚本不存在")
            return False
        
        if not RAW_PROMPTS_FILE.exists():
            self.logger.warning(f"原始 Prompt 文件不存在: {RAW_PROMPTS_FILE}")
            return False
        
        self.logger.info("启动炼金脚本...")
        
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(alchemist_script),
                    "--input", str(RAW_PROMPTS_FILE),
                    "--batch-size", "20"
                ],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.logger.info("炼金脚本执行成功")
                self.stats["processing_triggered"] = True
                return True
            else:
                self.logger.error(f"炼金脚本执行失败: {result.stderr}")
                self.stats["errors"].append(f"炼金脚本错误: {result.stderr[:200]}")
                return False
                
        except Exception as e:
            self.logger.error(f"执行炼金脚本时出错: {e}")
            self.stats["errors"].append(str(e))
            return False
    
    def _generate_report(self) -> None:
        """生成执行报告"""
        report_file = PROCESSED_DIR / "pipeline_report.json"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            **self.stats,
            "sources": [
                {
                    "owner": s.owner,
                    "repo": s.repo,
                    "description": s.description
                }
                for s in SOURCES
            ],
            "config": {
                "dry_run": self.dry_run,
                "output_file": str(RAW_PROMPTS_FILE),
            }
        }
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"报告已保存: {report_file}")


def main():
    parser = argparse.ArgumentParser(
        description="MUSICprompt 全自动数据摄取与炼金流水线"
    )
    parser.add_argument('--skip-fetch', action='store_true', help='跳过数据抓取阶段')
    parser.add_argument('--skip-process', action='store_true', help='跳过炼金处理阶段')
    parser.add_argument('--dry-run', action='store_true', help='试运行模式')
    
    args = parser.parse_args()
    
    setup_secure_logging(
        level=logging.INFO,
        log_format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    
    logger = logging.getLogger("main")
    
    try:
        runner = PipelineRunner(dry_run=args.dry_run)
        stats = runner.run(
            skip_fetch=args.skip_fetch,
            skip_process=args.skip_process
        )
        
        print("\n" + "=" * 60)
        print("执行摘要")
        print("=" * 60)
        print(f"开始时间: {stats['start_time']}")
        print(f"结束时间: {stats['end_time']}")
        print(f"抓取文件数: {stats['files_fetched']}")
        print(f"提取 Prompt: {stats['prompts_extracted']}")
        print(f"唯一 Prompt: {stats['prompts_unique']}")
        print(f"炼金触发: {'是' if stats['processing_triggered'] else '否'}")
        
        if stats['errors']:
            print(f"\n错误列表:")
            for err in stats['errors']:
                print(f"  - {err}")
        
        print("=" * 60)
        
    except KeyboardInterrupt:
        logger.warning("用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
