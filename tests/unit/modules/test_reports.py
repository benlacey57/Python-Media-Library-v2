import pytest
from core.database import Database
from modules.reports import ReportingModule


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_media.db"
    database = Database(db_path)
    database.initialize_db()
    return database


@pytest.fixture
def populated_db(db):
    cat_movie = db.get_or_create_category("Movie")
    db.insert_media_item({
        "category_id": cat_movie,
        "filename": "Sample.Movie.2023.mp4",
        "filepath": "/storage/movies/Sample.Movie.2023.mp4",
        "file_size_bytes": 2000000000,
        "file_size_human": "1.86 GB",
        "container_format": "mp4",
        "resolution": "1920x1080",
        "video_codec": "h264",
    })
    return db


def test_get_library_summary(populated_db):
    reporter = ReportingModule(populated_db)
    summary = reporter.get_library_summary()
    
    assert summary["total_files"] == 1
    assert summary["total_size_bytes"] == 2000000000
    assert "Movie" in summary["categories"]
