from core.database import Database
from core.audit import Audit

class SeriesSeeder:
    def __init__(self, db: Database, audit: Audit = None):
        self.db = db
        self.audit = audit

    def seed(self) -> dict:
        """Seeds sample TV series and seasons."""
        series_data = {
            "title": "Breaking Bad",
            "sort_title": "Breaking Bad",
            "imdb_id": "tt0903747",
            "release_year": 2008,
            "start_date": "2008-01-20",
            "end_date": "2013-09-29",
            "genre": "Crime, Drama, Thriller",
            "age_rating": "TV-MA",
            "total_seasons": 1,
            "total_episodes": 2,
            "overview": "A chemistry teacher turned methamphetamine kingpin.",
            "status": "Ended"
        }

        series_id = self.db.insert_series(series_data)

        # Seed Season 1
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO seasons (series_id, season_number, name, episode_count, overview)
                VALUES (?, ?, ?, ?, ?)
                """,
                (series_id, 1, "Season 1", 2, "The first season introduces Walter White.")
            )
            conn.commit()

        if self.audit:
            self.audit.log("Seeder", "SEED_SERIES", "SUCCESS", f"Seeded series ID {series_id}: Breaking Bad.")
        return {"series_id": series_id}
              
