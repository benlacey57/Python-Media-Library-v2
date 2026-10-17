from unittest.mock import MagicMock, patch
import pytest
from core.database import Database
from modules.imdb_sync import IMDbSync


@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_media.db"
    database = Database(db_path)
    database.initialize_db()
    return database


@patch("modules.imdb_sync.urllib.request.urlopen")
def test_connection_success(mock_urlopen, db):
    # Mock successful response
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    sync_service = IMDbSync(db, tmdb_api_key="fake_key")
    assert sync_service.test_connection() is True


@patch("modules.imdb_sync.urllib.request.urlopen")
def test_connection_failure(mock_urlopen, db):
    # Mock failure / exception
    mock_urlopen.side_effect = Exception("Connection error")

    sync_service = IMDbSync(db, tmdb_api_key="bad_key")
    assert sync_service.test_connection() is False
  
