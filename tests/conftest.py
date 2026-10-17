import pytest
from core.database import Database


@pytest.fixture
def db(tmp_path):
    """Provides a fresh, isolated temporary database for each test."""
    db_path = tmp_path / "test_media.sqlite"
    database = Database(db_path)
    database.initialize_db()
    return database


@pytest.fixture
def seeded_db(db):
    """Acts as a database seeder, pre-populating standard test entities."""
    # 1. Get or create categories
    cat_movie = db.get_or_create_category("Movie")
    cat_tv = db.get_or_create_category("TV Show")

    # 2. Seed a test series
    series_id = db.insert_series({
        "title": "Breaking Bad",
        "imdb_id": "tt0903747",
        "release_year": 2008,
        "total_seasons": 1,
        "overview": "A chemistry teacher turned drug kingpin.",
    })

    # 3. Seed a test media item (inefficient codec for optimizer testing)
    db.insert_media_item({
        "category_id": cat_tv,
        "series_id": series_id,
        "season_number": 1,
        "episode_number": 1,
        "filename": "Breaking.Bad.S01E01.mkv",
        "filepath": "/storage/media/Breaking.Bad.S01E01.mkv",
        "file_size_bytes": 350000000,
        "file_size_human": "333.79 MB",
        "container_format": "mkv",
        "resolution": "1920x1080",
        "video_codec": "h264",  # Inefficient codec for testing optimizer
        "audio_track_count": 1,
        "subtitle_track_count": 1,
    })

    return db
  
