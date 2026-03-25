#!/usr/bin/env python3
"""
新工作流主执行脚本
整合提取、翻译、格式化全流程
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_step(step_name: str, script_name: str) -> bool:
    """执行单个步骤"""
    print(f"\n{'='*60}")
    print(f"步骤: {step_name}")
    print(f"{'='*60}\n")
    
    script_path = Path(__file__).parent / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=False,
            text=True,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n步骤失败: {step_name}")
        print(f"错误: {e}")
        return False
    except Exception as e:
        print(f"\n步骤异常: {step_name}")
        print(f"错误: {e}")
        return False


def main():
    """主函数"""
    start_time = datetime.now()
    
    print("="*60)
    print("AI音乐提示词处理新工作流")
    print("="*60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    steps = [
        ("1. 提取高质量提示词", "prompt_extractor.py"),
        ("2. 翻译提示词", "prompt_translator.py"),
        ("3. 生成输出文件", "output_formatter.py"),
    ]
    
    completed = 0
    failed = 0
    
    for step_name, script_name in steps:
        if run_step(step_name, script_name):
            completed += 1
        else:
            failed += 1
            print(f"\n是否继续? (y/n): ", end="")
            # 自动继续
            print("y")
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print("\n" + "="*60)
    print("工作流执行完成")
    print("="*60)
    print(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"总耗时: {duration/60:.1f} 分钟")
    print(f"成功步骤: {completed}/{len(steps)}")
    print(f"失败步骤: {failed}/{len(steps)}")
    print("="*60)


if __name__ == "__main__":
    main()
