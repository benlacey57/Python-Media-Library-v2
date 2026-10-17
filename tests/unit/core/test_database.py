from pathlib import Path
import pytest
from core.database import Database
from core.models import SeriesModel


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test_media.db"


@pytest.fixture
def db(db_path):
    manager = Database(db_path)
    manager.initialize_db()
    return manager


def test_database_initialization(db_path):
    manager = Database(db_path)
    manager.initialize_db()
    assert db_path.exists()


def test_default_database_path():
    manager = Database()
    assert manager.db_path == str(Path("data/database.sqlite"))


def test_series_crud(db):
    series_data = {
        "title": "Breaking Bad",
        "imdb_id": "tt0903747",
        "release_year": 2008,
        "total_seasons": 5,
        "overview": "A chemistry teacher turned drug kingpin.",
    }
    series_id = db.insert_series(series_data)
    assert series_id is not None

    fetched = db.get_series_by_id(series_id)
    assert fetched is not None
    assert fetched["title"] == "Breaking Bad"
    assert fetched["imdb_id"] == "tt0903747"


def test_media_item_insertion(db):
    cat_id = db.get_or_create_category("TV Show")
    series_id = db.insert_series({
        "title": "Breaking Bad",
        "imdb_id": "tt0903747",
        "release_year": 2008,
        "total_seasons": 5,
    })

    item_data = {
        "category_id": cat_id,
        "series_id": series_id,
        "season_id": None,
        "filename": "Breaking.Bad.S01E01.mkv",
        "filepath": "/storage/movies/test/Breaking.Bad.S01E01.mkv",
        "file_size_bytes": 350000000,
        "file_size_human": "333.79 MB",
        "container_format": "mkv",
        "resolution": "1920x1080",
        "video_codec": "h264",
        "audio_track_count": 1,
        "subtitle_track_count": 1,
    }

    item_id = db.insert_media_item(item_data)
    assert item_id is not None

    items = db.get_media_items()
    assert len(items) == 1
    assert items[0]["filename"] == "Breaking.Bad.S01E01.mkv"


def test_pydantic_validation():
    valid_series = SeriesModel(
        title="Inception",
        imdb_id="tt1375666",
        release_year=2010,
        total_seasons=1,
    )
    assert valid_series.title == "Inception"

    with pytest.raises(Exception):
        SeriesModel(title="", release_year=-5)
        
