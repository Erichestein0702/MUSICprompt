#!/usr/bin/env python3
"""
Prompt 检索工具
支持全文搜索、流派筛选、评分筛选等功能
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.db.models import MusicPromptDB


def search_prompts(
    db: MusicPromptDB,
    query: str = None,
    genre: str = None,
    use_case: str = None,
    min_score: float = 0,
    limit: int = 20
):
    """搜索 Prompts"""
    results = []
    
    if query:
        print(f"\n搜索关键词: '{query}'")
        results = db.search(query, limit=limit)
    elif genre:
        print(f"\n流派筛选: {genre}")
        results = db.get_by_genre(genre, limit=limit)
    elif use_case:
        print(f"\n场景筛选: {use_case}")
        results = db.get_by_use_case(use_case, limit=limit)
    else:
        print(f"\n获取高分 Prompt (评分 >= {min_score})")
        all_results = db.get_top_rated(limit=limit * 2)
        results = [r for r in all_results if r['quality_score'] >= min_score][:limit]
    
    if min_score > 0 and results:
        results = [r for r in results if r['quality_score'] >= min_score]
    
    return results


def display_results(results: list):
    """显示搜索结果"""
    if not results:
        print("\n没有找到符合条件的 Prompt")
        return
    
    print(f"\n找到 {len(results)} 条结果:")
    print("=" * 60)
    
    for i, r in enumerate(results, 1):
        print(f"\n[{i}] {r.get('title', '未命名')}")
        print(f"    ID: {r.get('id')}")
        print(f"    评分: {r.get('quality_score', 0)}/10")
        print(f"    平台: {r.get('platform', 'unknown')}")
        
        prompt_text = r.get('prompt_text', '')
        if len(prompt_text) > 100:
            prompt_text = prompt_text[:100] + "..."
        print(f"    提示词: {prompt_text}")


def display_stats(db: MusicPromptDB):
    """显示统计信息"""
    stats = db.get_stats()
    
    print("\n" + "=" * 60)
    print("数据库统计")
    print("=" * 60)
    print(f"总 Prompt 数: {stats['total_prompts']}")
    print(f"流派数: {stats['total_genres']}")
    print(f"乐器数: {stats['total_instruments']}")
    print(f"使用场景数: {stats['total_use_cases']}")
    print(f"平均评分: {stats['avg_quality_score']}")
    
    print("\n热门流派:")
    for g in stats['top_genres'][:10]:
        print(f"  {g['name']}: {g['count']} 条")


def interactive_mode(db: MusicPromptDB):
    """交互模式"""
    print("\n" + "=" * 60)
    print("MUSICprompt 交互检索模式")
    print("=" * 60)
    print("输入 'help' 查看命令, 'quit' 退出")
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                print("再见!")
                break
            
            if user_input.lower() == 'help':
                print("""
命令帮助:
  search <关键词>     - 全文搜索
  genre <流派名>      - 按流派筛选
  usecase <场景名>    - 按使用场景筛选
  top [数量]          - 获取高分 Prompt
  stats               - 显示统计信息
  quit                - 退出
                """)
                continue
            
            if user_input.lower() == 'stats':
                display_stats(db)
                continue
            
            parts = user_input.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else None
            
            if cmd == 'search' and arg:
                results = db.search(arg, limit=20)
                display_results(results)
            elif cmd == 'genre' and arg:
                results = db.get_by_genre(arg, limit=20)
                display_results(results)
            elif cmd == 'usecase' and arg:
                results = db.get_by_use_case(arg, limit=20)
                display_results(results)
            elif cmd == 'top':
                limit = int(arg) if arg and arg.isdigit() else 20
                results = db.get_top_rated(limit=limit)
                display_results(results)
            else:
                print("未知命令。输入 'help' 查看帮助")
        
        except KeyboardInterrupt:
            print("\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="MUSICprompt 检索工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tools/search_prompts.py --query "electronic"
  python tools/search_prompts.py --genre pop --min-score 8
  python tools/search_prompts.py --use-case party
  python tools/search_prompts.py --interactive
        """
    )
    
    parser.add_argument('--query', '-q', help='搜索关键词')
    parser.add_argument('--genre', '-g', help='按流派筛选')
    parser.add_argument('--use-case', '-u', help='按使用场景筛选')
    parser.add_argument('--min-score', '-m', type=float, default=0, help='最低评分')
    parser.add_argument('--limit', '-l', type=int, default=20, help='结果数量限制')
    parser.add_argument('--stats', '-s', action='store_true', help='显示统计信息')
    parser.add_argument('--interactive', '-i', action='store_true', help='交互模式')
    parser.add_argument('--db', default='data/musicprompts.db', help='数据库路径')
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    db_path = project_root / args.db
    
    if not db_path.exists():
        print(f"数据库不存在: {db_path}")
        print("请先运行: python tools/import_to_db.py")
        return
    
    db = MusicPromptDB(str(db_path))
    
    try:
        if args.interactive:
            interactive_mode(db)
        elif args.stats:
            display_stats(db)
        else:
            results = search_prompts(
                db,
                query=args.query,
                genre=args.genre,
                use_case=args.use_case,
                min_score=args.min_score,
                limit=args.limit
            )
            display_results(results)
    finally:
        db.close()


if __name__ == "__main__":
    main()
