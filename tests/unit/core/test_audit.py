from pathlib import Path
import pytest
from core.database import Database
from core.audit import Audit


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_media.db"
    database = Database(db_path)
    database.initialize_db()
    return database


def test_audit_logging_and_search(db, tmp_path):
    log_file = tmp_path / "debug.log"
    config = {
        "audit_logging": {
            "log_to_file": True,
            "log_file_path": str(log_file),
            "log_level": "DEBUG"
        }
    }

    audit = Audit(db, config=config)
    audit.log("Analyzer", "SCAN_DIR", "SUCCESS", "Scanned 5 files successfully.")
    audit.log("Optimizer", "TRANSCODE", "ERROR", "FFmpeg process failed.")

    # Test retrieval
    entries = audit.get_entries()
    assert len(entries) == 2

    # Test search
    search_results = audit.search_entries("FFmpeg")
    assert len(search_results) == 1
    assert search_results[0]["module_name"] == "Optimizer"

    # Test summary
    summary = audit.get_summary()
    assert summary["levels"]["SUCCESS"] == 1
    assert summary["levels"]["ERROR"] == 1
    assert summary["modules"]["Analyzer"] == 1

    # Test timeline counts
    timeline = audit.get_timeline_counts(interval="date")
    assert len(timeline) >= 1
    assert timeline[0]["count"] == 2

    # Verify file logging occurred
    assert log_file.exists()
    log_content = log_file.read_text(encoding="utf-8")
    assert "Scanned 5 files successfully" in log_content
  
