import sqlite3
from pathlib import Path


class DatabaseManager:

  def __init__(self, db_path=None):
    if db_path is None:
      config_dir = Path("~/.config/media_manager").expanduser()
      config_dir.mkdir(parents=True, exist_ok=True)
      db_path = config_dir / "media.db"
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
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL
                );

                CREATE TABLE IF NOT EXISTS series (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    imdb_id TEXT UNIQUE,
                    release_year INTEGER,
                    start_date TEXT,
                    end_date TEXT,
                    genre TEXT,
                    age_rating TEXT,
                    total_seasons INTEGER,
                    overview TEXT
                );

                CREATE TABLE IF NOT EXISTS seasons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id INTEGER,
                    season_number INTEGER,
                    episode_count INTEGER,
                    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS media_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    series_id INTEGER,
                    category_id INTEGER,
                    filepath TEXT UNIQUE NOT NULL,
                    filename TEXT NOT NULL,
                    size_bytes INTEGER,
                    resolution TEXT,
                    video_codec TEXT,
                    audio_track_count INTEGER,
                    subtitle_track_count INTEGER,
                    is_optimized INTEGER DEFAULT 0,
                    is_renamed INTEGER DEFAULT 0,
                    analyzed_date TEXT,
                    FOREIGN KEY (series_id) REFERENCES series(id) ON DELETE SET NULL,
                    FOREIGN KEY (category_id) REFERENCES categories(id)
                );

                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    module TEXT,
                    level TEXT,
                    message TEXT
                );
            """)
      # Seed default categories
      conn.execute(
          "INSERT OR IGNORE INTO categories (name) VALUES ('TV Show')"
      )
      conn.execute("INSERT OR IGNORE INTO categories (name) VALUES ('Movie')")
      conn.commit()

  def get_or_create_category(self, name: str) -> int:
    with self.get_connection() as conn:
      cursor = conn.cursor(
          "SELECT id FROM categories WHERE name = ?", (name,)
      ).fetchone()
      if cursor:
        return cursor["id"]
      cursor = conn.execute(
          "INSERT INTO categories (name) VALUES (?)", (name,)
      )
      conn.commit()
      return cursor.lastrowid

  def insert_series(self, data: dict) -> int:
    with self.get_connection() as conn:
      cursor = conn.execute(
          """
                INSERT OR IGNORE INTO series (title, imdb_id, release_year, start_date, end_date, genre, age_rating, total_seasons, overview)
                VALUES (:title, :imdb_id, :release_year, :start_date, :end_date, :genre, :age_rating, :total_seasons, :overview)
            """,
          {
              "title": data.get("title"),
              "imdb_id": data.get("imdb_id"),
              "release_year": data.get("release_year"),
              "start_date": data.get("start_date"),
              "end_date": data.get("end_date"),
              "genre": data.get("genre"),
              "age_rating": data.get("age_rating"),
              "total_seasons": data.get("total_seasons"),
              "overview": data.get("overview"),
          },
      )
      conn.commit()
      if cursor.lastrowid:
        return cursor.lastrowid
      # If already exists by imdb_id, fetch id
      if data.get("imdb_id"):
        row = conn.execute(
            "SELECT id FROM series WHERE imdb_id = ?", (data["imdb_id"],)
        ).fetchone()
        if row:
          return row["id"]
      return 0

  def get_series_by_id(self, series_id: int):
    with self.get_connection() as conn:
      row = conn.execute(
          "SELECT * FROM series WHERE id = ?", (series_id,)
      ).fetchone()
      return dict(row) if row else None

  def insert_media_item(self, data: dict) -> int:
    with self.get_connection() as conn:
      cursor = conn.execute(
          """
                INSERT OR REPLACE INTO media_items 
                (series_id, category_id, filepath, filename, size_bytes, resolution, video_codec, audio_track_count, subtitle_track_count, is_optimized, is_renamed, analyzed_date)
                VALUES (:series_id, :category_id, :filepath, :filename, :size_bytes, :resolution, :video_codec, :audio_track_count, :subtitle_track_count, :is_optimized, :is_renamed, DATETIME('now'))
            """,
          data,
      )
      conn.commit()
      return cursor.lastrowid

  def get_media_items(self):
    with self.get_connection() as conn:
      rows = conn.execute("SELECT * FROM media_items").fetchall()
      return [dict(row) for row in rows]
      
