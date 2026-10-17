from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
from core.database import Database
from modules.analyzer import Analyzer
from modules.optimizer import Optimizer
from modules.renamer import Renamer
from modules.reports import ReportingModule


@pytest.fixture
def integration_env(tmp_path):
    # Setup mock media folder and files
    media_dir = tmp_path / "media_library"
    media_dir.mkdir()
    
    movie_file = media_dir / "Breaking.Bad.S01E01.[1080p].h264.mkv"
    movie_file.write_bytes(b"dummy video data")

    db_path = tmp_path / "integration.db"
    db = Database(db_path)
    db.initialize_db()
    
    return db, media_dir, movie_file


@patch("modules.analyzer.run_ffprobe")
def test_full_media_workflow(mock_ffprobe, integration_env):
    db, media_dir, movie_file = integration_env

    # Mock ffprobe metadata output for our test file
    mock_ffprobe.return_value = {
        "streams": [
            {"codec_type": "video", "codec_name": "h264", "width": 1920, "height": 1080},
            {"codec_type": "audio", "codec_name": "aac", "tags": {"language": "eng"}}
        ]
    }

    # 1. Test Analyzer Phase
    analyzer = Analyzer(db)
    scanned_count = analyzer.scan_directory(str(media_dir))
    assert scanned_count == 1

    items = db.get_media_items()
    assert len(items) == 1
    item = items[0]
    assert item["video_codec"] == "h264"

    # 2. Test Optimizer Phase (Mocking subprocess run for ffmpeg)
    with patch("modules.optimizer.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        optimizer = Optimizer(db, config={"inefficient_codecs": ["h264"]})
        opt_results = optimizer.optimize_media_items()
        
        assert len(opt_results) == 1
        assert opt_results[0]["status"] == "Success"
        assert opt_results[0]["action_type"] == "TRANSCODE_VIDEO"

    # 3. Test Renamer Phase
    renamer = Renamer(db, config={
        "filename_templates": {
            "tv_show": "{series_name}.S{season:02d}E{episode:02d}.{episode_title}"
        }
    })
    
    new_name = renamer.format_episode_name("Breaking Bad", 1, 1, "Pilot", ".mkv")
    assert new_name == "Breaking.Bad.S01E01.Pilot.mkv"

    # 4. Test Reporting Phase
    reporter = ReportingModule(db)
    summary = reporter.get_library_summary()
    quality = reporter.get_encoding_quality_report()

    assert summary["total_files"] == 1
    assert "h264" in quality["video_codecs"] or "libx265" in quality["video_codecs"]
    assert "1920x1080" in quality["resolutions"]
  
