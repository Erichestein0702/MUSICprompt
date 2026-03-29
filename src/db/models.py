"""
MUSICprompt 数据库模型定义
使用 SQLite 存储所有 Prompt 数据
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any


SCHEMA = """
-- 主表：Prompts
CREATE TABLE IF NOT EXISTS prompts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    title_zh TEXT,
    prompt_text TEXT NOT NULL,
    prompt_zh TEXT,
    platform TEXT,
    quality_score REAL DEFAULT 0,
    bpm INTEGER,
    key_signature TEXT,
    source TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 流派标签表
CREATE TABLE IF NOT EXISTS genres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_zh TEXT,
    parent_id INTEGER REFERENCES genres(id)
);

-- Prompt-流派关联表
CREATE TABLE IF NOT EXISTS prompt_genres (
    prompt_id TEXT REFERENCES prompts(id) ON DELETE CASCADE,
    genre_id INTEGER REFERENCES genres(id) ON DELETE CASCADE,
    PRIMARY KEY (prompt_id, genre_id)
);

-- 乐器表
CREATE TABLE IF NOT EXISTS instruments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_zh TEXT
);

-- Prompt-乐器关联表
CREATE TABLE IF NOT EXISTS prompt_instruments (
    prompt_id TEXT REFERENCES prompts(id) ON DELETE CASCADE,
    instrument_id INTEGER REFERENCES instruments(id) ON DELETE CASCADE,
    PRIMARY KEY (prompt_id, instrument_id)
);

-- 使用场景表
CREATE TABLE IF NOT EXISTS use_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_zh TEXT
);

-- Prompt-使用场景关联表
CREATE TABLE IF NOT EXISTS prompt_use_cases (
    prompt_id TEXT REFERENCES prompts(id) ON DELETE CASCADE,
    use_case_id INTEGER REFERENCES use_cases(id) ON DELETE CASCADE,
    PRIMARY KEY (prompt_id, use_case_id)
);

-- 情绪关键词表
CREATE TABLE IF NOT EXISTS moods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    name_zh TEXT
);

-- Prompt-情绪关联表
CREATE TABLE IF NOT EXISTS prompt_moods (
    prompt_id TEXT REFERENCES prompts(id) ON DELETE CASCADE,
    mood_id INTEGER REFERENCES moods(id) ON DELETE CASCADE,
    PRIMARY KEY (prompt_id, mood_id)
);

-- 索引优化
CREATE INDEX IF NOT EXISTS idx_prompts_quality ON prompts(quality_score DESC);
CREATE INDEX IF NOT EXISTS idx_prompts_platform ON prompts(platform);
CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_prompt_genres_prompt ON prompt_genres(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_instruments_prompt ON prompt_instruments(prompt_id);
CREATE INDEX IF NOT EXISTS idx_prompt_use_cases_prompt ON prompt_use_cases(prompt_id);

-- 全文搜索虚拟表
CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
    id,
    title,
    title_zh,
    prompt_text,
    prompt_zh,
    content='prompts',
    content_rowid='rowid'
);

-- 触发器：保持 FTS 索引同步
CREATE TRIGGER IF NOT EXISTS prompts_ai AFTER INSERT ON prompts BEGIN
    INSERT INTO prompts_fts(rowid, id, title, title_zh, prompt_text, prompt_zh)
    VALUES (new.rowid, new.id, new.title, new.title_zh, new.prompt_text, new.prompt_zh);
END;

CREATE TRIGGER IF NOT EXISTS prompts_ad AFTER DELETE ON prompts BEGIN
    INSERT INTO prompts_fts(prompts_fts, rowid, id, title, title_zh, prompt_text, prompt_zh)
    VALUES('delete', old.rowid, old.id, old.title, old.title_zh, old.prompt_text, old.prompt_zh);
END;

CREATE TRIGGER IF NOT EXISTS prompts_au AFTER UPDATE ON prompts BEGIN
    INSERT INTO prompts_fts(prompts_fts, rowid, id, title, title_zh, prompt_text, prompt_zh)
    VALUES('delete', old.rowid, old.id, old.title, old.title_zh, old.prompt_text, old.prompt_zh);
    INSERT INTO prompts_fts(rowid, id, title, title_zh, prompt_text, prompt_zh)
    VALUES (new.rowid, new.id, new.title, new.title_zh, new.prompt_text, new.prompt_zh);
END;
"""


class MusicPromptDB:
    """MUSICprompt 数据库管理类"""
    
    def __init__(self, db_path: str = "data/musicprompts.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
    
    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
    
    def init_db(self):
        """初始化数据库结构"""
        conn = self.connect()
        conn.executescript(SCHEMA)
        conn.commit()
        print(f"数据库已初始化: {self.db_path}")
    
    def insert_prompt(self, prompt: Dict[str, Any]) -> bool:
        """插入单条 Prompt"""
        conn = self.connect()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO prompts 
                (id, title, title_zh, prompt_text, prompt_zh, platform, quality_score, bpm, key_signature, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prompt.get('id'),
                prompt.get('title', ''),
                prompt.get('title_zh', ''),
                prompt.get('prompt_text', ''),
                prompt.get('prompt_zh', ''),
                prompt.get('platform', ''),
                prompt.get('quality_score', 0),
                prompt.get('bpm'),
                prompt.get('key'),
                prompt.get('source', '')
            ))
            
            prompt_id = prompt.get('id')
            
            for genre in prompt.get('genre', []):
                genre_id = self._get_or_create_genre(cursor, genre)
                cursor.execute(
                    "INSERT OR IGNORE INTO prompt_genres (prompt_id, genre_id) VALUES (?, ?)",
                    (prompt_id, genre_id)
                )
            
            for inst in prompt.get('instruments', []):
                inst_id = self._get_or_create_instrument(cursor, inst)
                cursor.execute(
                    "INSERT OR IGNORE INTO prompt_instruments (prompt_id, instrument_id) VALUES (?, ?)",
                    (prompt_id, inst_id)
                )
            
            for uc in prompt.get('use_cases', []):
                uc_id = self._get_or_create_use_case(cursor, uc)
                cursor.execute(
                    "INSERT OR IGNORE INTO prompt_use_cases (prompt_id, use_case_id) VALUES (?, ?)",
                    (prompt_id, uc_id)
                )
            
            moods = prompt.get('translation_meta', {}).get('mood_keywords_zh', [])
            for mood in moods:
                mood_id = self._get_or_create_mood(cursor, mood)
                cursor.execute(
                    "INSERT OR IGNORE INTO prompt_moods (prompt_id, mood_id) VALUES (?, ?)",
                    (prompt_id, mood_id)
                )
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"插入失败: {e}")
            conn.rollback()
            return False
    
    def _get_or_create_genre(self, cursor, name: str) -> int:
        cursor.execute("SELECT id FROM genres WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row['id']
        cursor.execute("INSERT INTO genres (name) VALUES (?)", (name,))
        return cursor.lastrowid
    
    def _get_or_create_instrument(self, cursor, name: str) -> int:
        cursor.execute("SELECT id FROM instruments WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row['id']
        cursor.execute("INSERT INTO instruments (name) VALUES (?)", (name,))
        return cursor.lastrowid
    
    def _get_or_create_use_case(self, cursor, name: str) -> int:
        cursor.execute("SELECT id FROM use_cases WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row['id']
        cursor.execute("INSERT INTO use_cases (name) VALUES (?)", (name,))
        return cursor.lastrowid
    
    def _get_or_create_mood(self, cursor, name: str) -> int:
        cursor.execute("SELECT id FROM moods WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return row['id']
        cursor.execute("INSERT INTO moods (name) VALUES (?)", (name,))
        return cursor.lastrowid
    
    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """全文搜索（使用 LIKE 简化实现）"""
        conn = self.connect()
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        cursor.execute("""
            SELECT * FROM prompts
            WHERE title LIKE ? 
               OR title_zh LIKE ? 
               OR prompt_text LIKE ? 
               OR prompt_zh LIKE ?
            ORDER BY quality_score DESC
            LIMIT ?
        """, (search_pattern, search_pattern, search_pattern, search_pattern, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_by_genre(self, genre: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """按流派筛选"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*
            FROM prompts p
            JOIN prompt_genres pg ON p.id = pg.prompt_id
            JOIN genres g ON pg.genre_id = g.id
            WHERE g.name = ?
            ORDER BY p.quality_score DESC
            LIMIT ? OFFSET ?
        """, (genre, limit, offset))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_by_use_case(self, use_case: str, limit: int = 50) -> List[Dict]:
        """按使用场景筛选"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT p.*
            FROM prompts p
            JOIN prompt_use_cases puc ON p.id = puc.prompt_id
            JOIN use_cases uc ON puc.use_case_id = uc.id
            WHERE uc.name = ?
            ORDER BY p.quality_score DESC
            LIMIT ?
        """, (use_case, limit))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_top_rated(self, limit: int = 20) -> List[Dict]:
        """获取最高评分"""
        conn = self.connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM prompts
            ORDER BY quality_score DESC
            LIMIT ?
        """, (limit,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_prompts_by_genre(self, genre: str, limit: int = 50) -> List[Dict]:
        """按流派筛选"""
        return self.get_by_genre(genre, limit=limit)
    
    def get_prompts_by_use_case(self, use_case: str, limit: int = 50) -> List[Dict]:
        """按使用场景筛选"""
        return self.get_by_use_case(use_case, limit=limit)
    
    def get_top_prompts(self, limit: int = 20) -> List[Dict]:
        """获取高分 Prompt"""
        return self.get_top_rated(limit=limit)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        conn = self.connect()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) as count FROM prompts")
        stats['total_prompts'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM genres")
        stats['total_genres'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM instruments")
        stats['total_instruments'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM use_cases")
        stats['total_use_cases'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT AVG(quality_score) as avg FROM prompts")
        stats['avg_quality_score'] = round(cursor.fetchone()['avg'] or 0, 2)
        
        cursor.execute("""
            SELECT g.name, COUNT(pg.prompt_id) as count
            FROM genres g
            JOIN prompt_genres pg ON g.id = pg.genre_id
            GROUP BY g.id
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['top_genres'] = [dict(row) for row in cursor.fetchall()]
        
        return stats


if __name__ == "__main__":
    db = MusicPromptDB()
    db.init_db()
    print("数据库初始化完成")
    print(db.get_stats())
