import os
from pathlib import Path
import pytest
from core.database import DatabaseManager
from core.models import MediaItemModel, SeriesModel


@pytest.fixture
def db_path(tmp_path):
  return tmp_path / "test_media.db"


@pytest.fixture
def db(db_path):
  manager = DatabaseManager(db_path)
  manager.initialize_db()
  return manager


def test_database_initialization(db_path):
  manager = DatabaseManager(db_path)
  manager.initialize_db()
  assert db_path.exists()


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
  # Insert parent category and series first
  cat_id = db.get_or_create_category("TV Show")
  series_id = db.insert_series({
      "title": "Breaking Bad",
      "imdb_id": "tt0903747",
      "release_year": 2008,
      "total_seasons": 5,
  })

  item_data = {
      "series_id": series_id,
      "category_id": cat_id,
      "filepath": "/storage/movies/test/Breaking.Bad.S01E01.mkv",
      "filename": "Breaking.Bad.S01E01.mkv",
      "size_bytes": 350000000,
      "resolution": "1920x1080",
      "video_codec": "h264",
      "is_optimized": 0,
      "is_renamed": 0,
  }

  item_id = db.insert_media_item(item_data)
  assert item_id is not None

  items = db.get_media_items()
  assert len(items) == 1
  assert items[0]["filename"] == "Breaking.Bad.S01E01.mkv"


def test_pydantic_validation():
  # Valid model test
  valid_series = SeriesModel(
      title="Inception",
      imdb_id="tt1375666",
      release_year=2010,
      total_seasons=1,
  )
  assert valid_series.title == "Inception"

  # Invalid model test (e.g., negative release year or missing title)
  with pytest.raises(Exception):
    SeriesModel(title="", release_year=-5)
    
