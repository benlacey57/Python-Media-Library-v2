from pathlib import Path
import pytest
from core.database import Database
from modules.renamer import Renamer


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_media.db"
    database = Database(db_path)
    database.initialize_db()
    return database


def test_clean_filename():
    renamer = Renamer(None)
    
    # Test cleaning brackets and whitespace
    raw_name = "Breaking.Bad.S01E01.[1080p].[HEVC]-ReleaseGroup.mkv"
    cleaned = renamer.clean_filename(raw_name)
    assert cleaned == "Breaking.Bad.S01E01.mkv"


def test_format_episode_filename():
    renamer = Renamer(None)
    
    # Test SxxExx formatting
    formatted = renamer.format_episode_name("Breaking Bad", 1, 1, "Pilot", ".mkv")
    assert formatted == "Breaking.Bad.S01E01.Pilot.mkv"
  
