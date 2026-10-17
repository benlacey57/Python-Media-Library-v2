import sqlite3
from pathlib import Path


class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            data_dir = Path("data")
            data_dir.mkdir(parents=True, exist_ok=True)
            db_path = data_dir / "database.sqlite"
        self.db_path = str(db_path)

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def initialize_db(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS series (
                    series_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    sort_title TEXT,
                    imdb_id TEXT UNIQUE,
                    release_year INTEGER,
                    start_date TEXT,
                    end_date TEXT,
                    genre TEXT,
                    age_rating TEXT,
                    total_seasons INTEGER DEFAULT 0,
                    total_episodes INTEGER DEFAULT 0,
                    overview TEXT,
                    poster_path TEXT,
                    status TEXT
                );

                CREATE TABLE IF NOT EXISTS seasons (
                    season_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id INTEGER NOT NULL,
                    season_number INTEGER NOT NULL,
                    name TEXT,
                    episode_count INTEGER DEFAULT 0,
                    overview TEXT,
                    FOREIGN KEY (series_id) REFERENCES series(series_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS media_items (
                    media_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_id INTEGER NOT NULL,
                    series_id INTEGER NULL,
                    season_id INTEGER NULL,
                    filename TEXT NOT NULL,
                    filepath TEXT UNIQUE NOT NULL,
                    file_size_bytes INTEGER NOT NULL,
                    file_size_human TEXT NOT NULL,
                    container_format TEXT,
                    duration_seconds REAL DEFAULT 0,
                    resolution TEXT,
                    video_codec TEXT,
                    video_profile TEXT,
                    bitrate_kbps INTEGER,
                    framerate REAL,
                    audio_track_count INTEGER DEFAULT 0,
                    subtitle_track_count INTEGER DEFAULT 0,
                    season_number INTEGER NULL,
                    episode_number INTEGER NULL,
                    episode_title TEXT NULL,
                    episode_overview TEXT NULL,
                    air_date TEXT NULL,
                    external_subtitle_path TEXT NULL,
                    analyzed_date TEXT NOT NULL,
                    last_modified_date TEXT NOT NULL,
                    optimization_status TEXT DEFAULT 'Pending',
                    naming_status TEXT DEFAULT 'Pending',
                    FOREIGN KEY (category_id) REFERENCES categories(category_id),
                    FOREIGN KEY (series_id) REFERENCES series(series_id) ON DELETE SET NULL,
                    FOREIGN KEY (season_id) REFERENCES seasons(season_id) ON DELETE SET NULL
                );

                CREATE TABLE IF NOT EXISTS audio_tracks (
                    audio_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    codec_name TEXT,
                    language TEXT,
                    channels INTEGER,
                    title TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    is_forced BOOLEAN DEFAULT 0,
                    FOREIGN KEY (media_id) REFERENCES media_items(media_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS subtitle_tracks (
                    subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    codec_name TEXT,
                    language TEXT,
                    title TEXT,
                    is_default BOOLEAN DEFAULT 0,
                    is_forced BOOLEAN DEFAULT 0,
                    is_external BOOLEAN DEFAULT 0,
                    FOREIGN KEY (media_id) REFERENCES media_items(media_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS file_optimizations (
                    optimization_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    media_id INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    details TEXT,
                    executed_date TEXT,
                    FOREIGN KEY (media_id) REFERENCES media_items(media_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS missing_episodes (
                    missing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id INTEGER NOT NULL,
                    season_number INTEGER NOT NULL,
                    episode_number INTEGER NOT NULL,
                    episode_title TEXT,
                    air_date TEXT,
                    overview TEXT,
                    FOREIGN KEY (series_id) REFERENCES series(series_id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS report_snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_period TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    metrics_json TEXT NOT NULL,
                    created_date TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    module_name TEXT NOT NULL,
                    action TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
            """)
            conn.execute("INSERT OR IGNORE INTO categories (name) VALUES ('TV Show')")
            conn.execute("INSERT OR IGNORE INTO categories (name) VALUES ('Movie')")
            conn.commit()

    def get_or_create_category(self, name: str) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT category_id FROM categories WHERE name = ?", (name,)).fetchone()
            if cursor:
                return cursor["category_id"]
            cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid

    def insert_series(self, data: dict) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO series (title, sort_title, imdb_id, release_year, start_date, end_date, genre, age_rating, total_seasons, total_episodes, overview, status)
                VALUES (:title, :sort_title, :imdb_id, :release_year, :start_date, :end_date, :genre, :age_rating, :total_seasons, :total_episodes, :overview, :status)
            """,
                {
                    "title": data.get("title"),
                    "sort_title": data.get("sort_title"),
                    "imdb_id": data.get("imdb_id"),
                    "release_year": data.get("release_year"),
                    "start_date": data.get("start_date"),
                    "end_date": data.get("end_date"),
                    "genre": data.get("genre"),
                    "age_rating": data.get("age_rating"),
                    "total_seasons": data.get("total_seasons", 0),
                    "total_episodes": data.get("total_episodes", 0),
                    "overview": data.get("overview"),
                    "status": data.get("status"),
                },
            )
            conn.commit()
            if cursor.lastrowid:
                return cursor.lastrowid
            if data.get("imdb_id"):
                row = conn.execute("SELECT series_id FROM series WHERE imdb_id = ?", (data["imdb_id"],)).fetchone()
                if row:
                    return row["series_id"]
            return 0

    def get_series_by_id(self, series_id: int):
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM series WHERE series_id = ?", (series_id,)).fetchone()
            return dict(row) if row else None

    def insert_media_item(self, data: dict) -> int:
        with self.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT OR REPLACE INTO media_items 
                (category_id, series_id, season_id, filename, filepath, file_size_bytes, file_size_human, container_format, resolution, video_codec, audio_track_count, subtitle_track_count, analyzed_date, last_modified_date)
                VALUES (:category_id, :series_id, :season_id, :filename, :filepath, :file_size_bytes, :file_size_human, :container_format, :resolution, :video_codec, :audio_track_count, :subtitle_track_count, DATETIME('now'), DATETIME('now'))
            """,
                data,
            )
            conn.commit()
            return cursor.lastrowid

    def get_media_items(self):
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM media_items").fetchall()
            return [dict(row) for row in rows]
            
