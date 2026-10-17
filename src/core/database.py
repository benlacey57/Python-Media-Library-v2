from pathlib import Path
import sqlite3


class Database:
    def __init__(self, db_path: Path = Path("data/media_library.sqlite")):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    def get_connection(self):
        """Returns a database connection with sqlite3.Row row_factory enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_db(self):
        """Initializes the database schema."""
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
            """)
            conn.commit()

    def get_media_items(self):
        """Retrieves all media items joined with their category names."""
        with self.get_connection() as conn:
            return conn.execute("""
                SELECT m.*, c.name as category 
                FROM media_items m 
                JOIN categories c ON m.category_id = c.category_id
            %s""" % "").fetchall()

    def insert_media_item(self, data: dict) -> int:
        """Inserts or replaces a media item record."""
        data.setdefault("series_id", None)
        data.setdefault("season_id", None)
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO media_items 
                (category_id, series_id, season_id, filename, filepath, file_size_bytes, file_size_human, container_format, resolution, video_codec, audio_track_count, subtitle_track_count, analyzed_date, last_modified_date)
                VALUES (:category_id, :series_id, :season_id, :filename, :filepath, :file_size_bytes, :file_size_human, :container_format, :resolution, :video_codec, :audio_track_count, :subtitle_track_count, DATETIME('now'), DATETIME('now'))
            """, data)
            conn.commit()
            return cursor.lastrowid

    def insert_series(self, data: dict) -> int:
        """Inserts or replaces a TV series record."""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO series 
                (title, sort_title, imdb_id, release_year, start_date, end_date, genre, age_rating, total_seasons, total_episodes, overview, poster_path, status)
                VALUES (:title, :sort_title, :imdb_id, :release_year, :start_date, :end_date, :genre, :age_rating, :total_seasons, :total_episodes, :overview, :poster_path, :status)
            """, data)
            conn.commit()
            return cursor.lastrowid

    def get_series(self, series_id: int):
        """Retrieves a series by its ID."""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM series WHERE series_id = ?", (series_id,)).fetchone()
            return dict(row) if row else None

    def get_or_create_category(self, name: str) -> int:
        """Retrieves or creates a media category ID."""
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT category_id FROM categories WHERE name = ?", (name,))
            row = cursor.fetchone()
            if row:
                return row["category_id"]
            cursor = conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
            conn.commit()
            return cursor.lastrowid
                                  
