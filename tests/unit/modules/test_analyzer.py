from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from core.database import Database
from modules.analyzer import Analyzer


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_media.db"
    database = Database(db_path)
    database.initialize_db()
    return database


SAMPLE_FFPROBE_OUTPUT = {
    "format": {"duration": "7200.5", "format_name": "matroska"},
    "streams": [
        {
            "codec_type": "video",
            "codec_name": "h264",
            "width": 1920,
            "height": 1080,
            "bit_rate": "5000000",
            "r_frame_rate": "24/1",
        },
        {
            "codec_type": "audio",
            "codec_name": "aac",
            "channels": 2,
            "tags": {"language": "eng", "title": "Stereo"},
        },
        {
            "codec_type": "subtitle",
            "codec_name": "subrip",
            "tags": {"language": "eng"},
        },
    ],
}

@patch("modules.analyzer.run_ffprobe")
def test_analyzer_scan(mock_ffprobe, db, tmp_path):
    mock_ffprobe.return_value = {
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1280, "height": 720},
            {"codec_type": "audio", "codec_name": "aac", "tags": {"language": "eng"}}
        ]
    }

    dummy_file = tmp_path / "Movie.2023.mp4"
    dummy_file.write_bytes(b"dummy data")

    analyzer = Analyzer(db)
    count = analyzer.scan_directory(str(tmp_path))

    assert count == 1
    items = db.get_media_items()
    assert len(items) == 1
    assert items[0]["filename"] == "Movie.2023.mp4"
    assert items[0]["video_codec"] == "h264"
    
@patch("modules.analyzer.subprocess.run")
def test_extract_metadata(mock_run, db, tmp_path):
    # Mock ffprobe subprocess response
    mock_result = MagicMock()
    import json
    mock_result.stdout = json.dumps(SAMPLE_FFPROBE_OUTPUT)
    mock_run.return_value = mock_result

    # Create a dummy media file
    dummy_file = tmp_path / "Inception.2010.1080p.mkv"
    dummy_file.write_bytes(b"fake media content bytes" * 100)

    analyzer = Analyzer(db)
    meta = analyzer.extract_metadata(dummy_file)

    assert meta is not None
    assert meta.filename == "Inception.2010.1080p.mkv"
    assert meta.video_codec == "h264"
    assert meta.resolution == "1920x1080"
    assert meta.audio_track_count == 1
    assert meta.subtitle_track_count == 1
    assert meta.category == "Movie"
