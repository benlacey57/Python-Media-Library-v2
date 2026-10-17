from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from core.database import Database
from modules.optimizer import Optimizer


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_media.db"
    database = Database(db_path)
    database.initialize_db()
    return database


@pytest.fixture
def seeded_db(db, tmp_path):
    """Fixture to seed the database with a sample movie and file for optimization tests."""
    cat_id = db.get_or_create_category("Movie")
    dummy_file = tmp_path / "sample_movie.mp4"
    dummy_file.write_bytes(b"dummy video data")

    item_data = {
        "category_id": cat_id,
        "filename": "sample_movie.mp4",
        "filepath": str(dummy_file),
        "file_size_bytes": 1000000000,
        "file_size_human": "953.67 MB",
        "container_format": "mp4",
        "resolution": "1920x1080",
        "video_codec": "h264",  # Inefficient codec triggering transcode
        "audio_track_count": 1,
        "subtitle_track_count": 1,
    }
    db.insert_media_item(item_data)
    return db


@patch("modules.optimizer.subprocess.run")
def test_optimizer_transcode_plan(mock_run, seeded_db):
    mock_run.return_value = MagicMock(returncode=0)

    # Pass configuration with root-level inefficient_codecs
    optimizer = Optimizer(seeded_db, config={
        "inefficient_codecs": ["h264", "mpeg4"],
        "tv_settings": {"preferred_video_codec": "libx265"},
        "movie_settings": {"preferred_video_codec": "libx265"}
    })

    results = optimizer.optimize_media_items()
    assert len(results) == 1
    assert results[0]["status"] == "Success"
    assert results[0]["action_type"] == "TRANSCODE_VIDEO"
    
