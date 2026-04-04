"""
MUSICprompt 共享常量定义
集中管理所有跨模块使用的常量，避免重复定义
"""

GENRE_ICONS = {
    "pop": "\U0001f3a4",
    "rock": "\U0001f3b8",
    "electronic": "\U0001f3b9",
    "hip-hop": "\U0001f3a4",
    "rap": "\U0001f3a4",
    "jazz": "\U0001f3b7",
    "blues": "\U0001f3b5",
    "classical": "\U0001f3bb",
    "folk": "\U0001f395",
    "country": "\U0001f9e0",
    "r&b": "\U0001f3b6",
    "soul": "\U0001f3ba",
    "funk": "\U0001f3b8",
    "metal": "\U0001f918",
    "punk": "\U0001f3b8",
    "ambient": "\U0001f319",
    "lo-fi": "\U0001f4fb",
    "house": "\U0001f3e0",
    "techno": "\U0001f3cb\ufe0f",
    "trap": "\U0001f3af",
    "dubstep": "\U0001f4a5",
    "trance": "\u2728",
}

USE_CASE_NAMES = {
    "party": "派对聚会",
    "study": "学习专注",
    "gaming": "游戏电竞",
    "cinematic": "影视配乐",
    "meditation": "冥想放松",
    "workout": "健身运动",
    "sleep": "睡眠休息",
    "general": "通用场景",
}

MUSIC_KEYWORDS = [
    "bpm", "key", "genre", "style", "tempo", "beat", "melody",
    "bass", "drum", "synth", "vocal", "guitar", "piano",
    "electronic", "ambient", "cinematic", "hip hop", "rock",
    "pop", "jazz", "classical", "lo-fi", "lofi", "trap",
    "house", "techno", "dubstep", "trance", "r&b", "folk",
    "orchestral", "acoustic", "instrumental", "vocal",
    "upbeat", "chill", "dark", "bright", "energetic", "calm",
    "epic", "emotional", "dramatic", "peaceful", "intense",
    "male vocals", "female vocals", "choir", "backing vocals",
    "reverb", "delay", "compression", "eq", "mix",
    "intro", "verse", "chorus", "bridge", "outro",
    "suno", "udio", "ai music", "music generation",
]

TECH_KEYWORDS = [
    "bpm", "key", "tempo", "major", "minor", "scale",
    "reverb", "compression", "saturation", "eq",
    "808", "kick", "snare", "hihat", "bass", "synth",
]

INSTRUMENTS = [
    "guitar", "piano", "violin", "drums", "bass", "synth",
    "keyboard", "flute", "saxophone", "trumpet", "cello",
    "harp", "ukulele", "mandolin", "banjo", "hurdy-gurdy",
]

GENRES = [
    "rock", "pop", "hip hop", "rap", "electronic", "edm",
    "jazz", "blues", "classical", "folk", "country", "r&b",
    "soul", "funk", "metal", "punk", "indie", "ambient",
    "lo-fi", "trap", "house", "techno", "trance", "dubstep",
]

STRUCTURE_TAGS = [
    "[intro]", "[verse]", "[chorus]", "[bridge]", "[outro]",
    "[hook]", "[pre-chorus]", "[interlude]", "[break]",
    "[solo]", "[build]", "[drop]",
]

SCENARIO_MAP = {
    "workout": ["gym", "workout", "exercise", "fitness", "training"],
    "study": ["study", "focus", "concentration", "lo-fi", "ambient"],
    "gaming": ["game", "gaming", "epic", "battle", "action"],
    "cinematic": ["cinematic", "film", "movie", "soundtrack", "score"],
    "meditation": ["meditation", "yoga", "relax", "calm", "peaceful"],
    "party": ["party", "dance", "club", "festival", "celebration"],
    "sleep": ["sleep", "dream", "night", "lullaby", "peaceful"],
}
