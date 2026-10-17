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
def test_test_connection_success(mock_urlopen, db):
    mock_response = MagicMock()
    mock_response.status = 200
    mock_urlopen.return_value.__enter__.return_value = mock_response

    sync_service = IMDbSync(db, tmdb_api_key="fake_key")
    assert sync_service.test_connection() is True


@patch("modules.imdb_sync.urllib.request.urlopen")
def test_test_connection_failure(mock_urlopen, db):
    mock_urlopen.side_effect = Exception("Connection error")

    sync_service = IMDbSync(db, tmdb_api_key="bad_key")
    assert sync_service.test_connection() is False


@patch("modules.imdb_sync.urllib.request.urlopen")
def test_sync_series_metadata(mock_urlopen, db):
    # Mock TMDB search result and TV show detail results
    search_mock = MagicMock()
    search_mock.read.return_value = b'{"results": [{"id": 1396, "name": "Breaking Bad"}]}'
    search_mock.status = 200

    detail_mock = MagicMock()
    detail_mock.read.return_value = b'{"id": 1396, "name": "Breaking Bad", "number_of_seasons": 1, "seasons": [{"season_number": 1, "episode_count": 2}]}'
    detail_mock.status = 200

    episode_mock = MagicMock()
    episode_mock.read.return_value = b'{"episodes": [{"episode_number": 1, "name": "Pilot", "air_date": "2008-01-20"}, {"episode_number": 2, "name": "Cat\'s in the Bag", "air_date": "2008-01-27"}]}'
    episode_mock.status = 200

    mock_urlopen.return_value.__enter__.side_effect = [search_mock, detail_mock, episode_mock]

    sync_service = IMDbSync(db, tmdb_api_key="fake_key")
    series_id = sync_service.sync_series("Breaking Bad")

    assert series_id is not None
    series = db.get_series_by_id(series_id)
    assert series["title"] == "Breaking Bad"
    assert series["total_seasons"] == 1
    
