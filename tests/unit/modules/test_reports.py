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


class ReportingModule:

    def __init__(self, db: Database):
        self.db = db

    def get_library_summary(self) -> dict:
        """Computes aggregate library statistics directly from the database."""
        with self.db.get_connection() as conn:
            total_files = conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0]
            total_size = conn.execute("SELECT SUM(file_size_bytes) FROM media_items").fetchone()[0] or 0
            
            cat_rows = conn.execute("""
                SELECT c.name as category_name, COUNT(m.media_id) as count, SUM(m.file_size_bytes) as size
                FROM media_items m
                JOIN categories c ON m.category_id = c.category_id
                GROUP BY c.name
            """).fetchall()

            categories = {}
            for row in cat_rows:
                categories[row["category_name"]] = {
                    "count": row["count"],
                    "size_bytes": row["size"]
                }

        return {
            "total_files": total_files,
            "total_size_bytes": total_size,
            "categories": categories,
        }

    def get_missing_episodes_report(self) -> list:
        """Retrieves all tracked missing episodes across series."""
        with self.db.get_connection() as conn:
            rows = conn.execute("""
                SELECT m.*, s.title as series_title 
                FROM missing_episodes m
                JOIN series s ON m.series_id = s.series_id
            """).fetchall()
            return [dict(row) for row in rows]

    def test_get_library_summary(populated_db):
        reporter = ReportingModule(populated_db)
        summary = reporter.get_library_summary()
    
        assert summary["total_files"] == 1
        assert summary["total_size_bytes"] == 2000000000
        assert "Movie" in summary["categories"]


    def test_get_encoding_quality_report(populated_db):
        reporter = ReportingModule(populated_db)
        report = reporter.get_encoding_quality_report()

        assert "mp4" in report["extensions"]
        assert report["extensions"]["mp4"]["count"] == 1
        assert report["video_codecs"]["h264"] == 1
        assert report["resolutions"]["1920x1080"] == 1
            
