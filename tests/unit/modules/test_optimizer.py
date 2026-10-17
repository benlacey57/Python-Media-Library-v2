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


@patch("modules.optimizer.subprocess.run")
def test_optimizer_transcode_plan(mock_run, db, tmp_path):
    mock_run.return_value = MagicMock(returncode=0)

    # Insert a dummy media item with an inefficient codec
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
        "video_codec": "h264",  # Inefficient codec
        "audio_track_count": 1,
        "subtitle_track_count": 1,
    }
    db.insert_media_item(item_data)

    optimizer = Optimizer(db, config={
        "tv_settings": {"preferred_video_codec": "libx265", "inefficient_codecs": ["h264"]},
        "movie_settings": {"preferred_video_codec": "libx265", "inefficient_codecs": ["h264"]}
    })

    # Run optimization check/execution
    results = optimizer.optimize_media_items()
    assert len(results) == 1
    assert results[0]["status"] == "Success"
  
